
import sys
import selectors
import json
import io
import struct
import re
import random
from import_database import read_correct_answer, read_questions
from models.player import Player


questions_data = read_questions()
correct_answer_data = read_correct_answer()
player_data = {
    "cookie": {
        "name": "username",
        "questions": [1, 2, 3, 4],
        'answers': ["", "", "", ""],
        "ingame": True,
        "score": 0,
        "win": False,
        "isPass": False
    }
}
player_order = []


def count_players():
    return len(player_data)-1


def create_new_player(username, cookie):
    new_player = Player(username=username, cookie=cookie)
    return new_player


def check_username_valid(username):
    if len(username) > 10:
        return False
    pattern = "[a-zA-Z0-9_]"
    for c in username:
        result = re.match(pattern, c)
        if not result:
            return False
    return True


def check_exist_username(username):
    list_player = player_data.values()
    for player in list_player:
        if player.get("name") == username:
            return True
    return False


class Message:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            print("sending", repr(self._send_buffer), "to", self.addr)
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                # Close when the buffer is drained. The response has been sent.
                if sent and not self._send_buffer:
                    self.close()

    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message(
        self, *, content_bytes, content_type, content_encoding
    ):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def _create_response_json_content(self):
        action = self.request.get("action")

        # action get_question
        if action == "get_question":
            req = json.loads(self.request["value"])
            cookies = req.get("cookie")
            player = player_data.get(cookies)
            ques = player["questions"]
            query = str(random.randint(1, 121))
            ques.append(query)
            answer = questions_data.get(query)
            content = {"result": answer}

        # action join
        elif action == "join":
            req = json.loads(self.request.get("value"))
            username = req["username"]
            cookies = req["cookie"]
            if not check_username_valid(username) or check_exist_username(username):
                content = {
                    "result": {'accepted': False}}
            else:
                player = create_new_player(username, cookies)
                if cookies not in player_order:
                    player_order.append(cookies)
                print(player_order)
                player_data[cookies] = dict(
                    name=username, questions=[], answers=[], ingame=True, score=0, win=False, isPass=False)
                print("total:", len(player_order), "players")
                content = {
                    "result": {'accepted': True, 'order': player_order.index(cookies)+1, 'player': len(player_order)}}

        # action answer_question
        elif action == 'answer_question':
            req = json.loads(self.request.get("value"))
            cookies = req.get("cookie")
            ans = req.get("answer")

            player = player_data.get(cookies)
            score = player.get("score")
            player["score"] = score + 1
            answer = player["answers"]
            answer.append(ans)
            if (correct_answer_data[player.get("questions")[-1]] == ans):
                score = player["score"]
                player["score"] = score + 1
                player_order.append(player_order.pop(0))
                content = {"result": {"correct": True, "score": player.get("score")}}
            else:
                player["ingame"] = False
                player_order.remove(cookies)
                content = {"result": {"correct":False}}

        # action next_question
        elif action == 'next_question':
            req = json.loads(self.request.get("value"))
            cookies = req.get("cookie")
            player = player_data.get(cookies)
            player["isPass"]=True
            score = player.get("score")
            player["score"] = score + 1
            answer = player["answers"]
            answer.append("NEXT_QUESTION")
            player_order.append(player_order.pop(0))
            content = {"result": {"correct": True, "score": player.get("score")}}

        elif action == 'get_status':
            req = json.loads(self.request["value"])
            cookies = req.get("cookie")
            player = player_data.get(cookies)
            score = player.get("score")
            if cookies not in player_order:
                content = {"result": False}
            else:
                if cookies in player_order and cookies == player_order[0]:
                    content = {"result": {"total_player": len(
                        player_order), "order": player_order.index(cookies)+1, "turn": True, "score": score, "ispass": player.get("isPass")}}
                else:
                    content = {"result": {"total_player": len(
                        player_order), "order": player_order.index(cookies)+1, "turn": False, "score": score, "ispass": player.get("isPass")}}
        elif action == 'get_leaderboard':
            req = json.loads(self.request["value"])
            all_player_data = player_data.values()
            leaderboard = []
            for player in all_player_data:
                name = player.get("name")
                userscore = player.get("score")
                leaderboard.append([name,str(userscore)])
            leaderboard.sort(key=lambda x: x[1], reverse=True)
            for i in range(len(leaderboard)):
                leaderboard[i].insert(0,str(i+1))
            content={"result":leaderboard}

        # else
        else:
            content = {"result": f'Error: invalid action "{action}".'}
        content_encoding = "utf-8"
        response = {
            "content_bytes": self._json_encode(content, content_encoding),
            "content_type": "text/json",
            "content_encoding": content_encoding,
        }
        return response

    def _create_response_binary_content(self):
        response = {
            "content_bytes": b"First 10 bytes of request: "
            + self.request[:10],
            "content_type": "binary/custom-server-binary-type",
            "content_encoding": "binary",
        }
        return response

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        self._read()

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_jsonheader()

        if self.jsonheader:
            if self.request is None:
                self.process_request()

    def write(self):
        if self.request:
            if not self.response_created:
                self.create_response()

        self._write()
        # self.response_created = False

    def close(self):
        print("closing connection to", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

    def process_request(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.request = self._json_decode(data, encoding)
            print("received request", repr(self.request), "from", self.addr)
        else:
            # Binary or unknown content-type
            self.request = data
            print(
                f'received {self.jsonheader["content-type"]} request from',
                self.addr,
            )
        # Set selector to listen for write events, we're done reading.
        self._set_selector_events_mask("w")

    def create_response(self):
        if self.jsonheader["content-type"] == "text/json":
            response = self._create_response_json_content()
        else:
            # Binary or unknown content-type
            response = self._create_response_binary_content()
        message = self._create_message(**response)
        self.response_created = True
        self._send_buffer += message
