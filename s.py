import socket
import argparse
import threading
import time

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Data
import player_model
import bubble_model


host = "127.0.0.1"
port = 4000
user_list = {}
notice_flag = 0

BUBBLE_COUNT = 10
BUBBLE_POS_OFFSET = 140

def generate_bubbles() -> bubble_model.Bubbles:
    bs_obj = bubble_model.Bubbles()
    for i in range(BUBBLE_COUNT):
        vec = bubble_model.Vec2(x=i*BUBBLE_POS_OFFSET, y=0)
        bm = bubble_model.Bubble(
            uid=i,
            pos_cur=vec,
            pos_target=vec,
            speed=0.0,
            type=bubble_model.BubbleType.normal)
        bs_obj.bubbles.append(bm)
    return bs_obj

def handle_receive(client_socket, addr, user):
    while True:
        buf = client_socket.recv(1024)
        print(buf)
        # res = Player.Player.GetRootAsPlayer(buf, 0)
        # print(res.Uid())
        # print(res.Username())
        # print(res.ImageUrl())
        # print(res.Score())
        # print(res.Status())
        time.sleep(0.1)
        # for con in user_list.values():
        #     try:
        #         con.sendall(data)
        #     except:
        #         print("연결이 비 정상적으로 종료된 소켓 발견")

    del user_list[user]
    client_socket.close()

def handle_notice(client_socket, addr, user):
    while True:
        req = request_packet_builder(Command.Command.ping, Sender.Sender.server)
        client_socket.send(req)

        buf = client_socket.recv(1024)
        print(buf)
        res= Response.Response.GetRootAsResponse(buf, 0)
        print(res.Timestamp())
        print(res.Command())
        print(res.ErrorCode())
        print(res.Data())
        if res.Command() == Command.Command.ping and res.ErrorCode() == 0:
            print('ping ok')
        time.sleep(1)

def accept_func():
    #IPv4 체계, TCP 타입 소켓 객체를 생성
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #포트를 사용 중 일때 에러를 해결하기 위한 구문
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #ip주소와 port번호를 함께 socket에 바인드 한다.
    #포트의 범위는 1-65535 사이의 숫자를 사용할 수 있다.
    server_socket.bind((host, port))

    #서버가 최대 5개의 클라이언트의 접속을 허용한다.
    server_socket.listen(5)

    player_list = player_model.Players()
    bubble_list = generate_bubbles()
    print(bubble_list)

    while True:
        try:
            #클라이언트 함수가 접속하면 새로운 소켓을 반환한다.
            client_socket, addr = server_socket.accept()
        except KeyboardInterrupt:
            for user, con in user_list:
                con.close()
            server_socket.close()
            print("Keyboard interrupt")
            break
        user = client_socket.recv(1024)
        print(user)
        user_list[user] = client_socket
        print(user_list)

        req = request_packet_builder(Command.Command.welcome, Sender.Sender.server)
        client_socket.send(req)

        buf = client_socket.recv(1024)
        print(buf)
        res= Response.Response.GetRootAsResponse(buf, 0)
        print(res.Timestamp())
        print(res.Command())
        print(res.ErrorCode())
        print(res.Data())
        if res.Command() == Command.Command.welcome and res.ErrorCode() == 0:
            player = Player.Player()
            player.Init(res.Data().Bytes, res.Data().Pos)
            pm = player_model.Player(
                uid=player.Uid(),
                username=player.Username(),
                image_url=player.ImageUrl(),
                score=player.Score(),
                status=player.Status())
            print(pm)
            player_list.players.append(pm)
            print(player_list)
            print('success contact')
            
        else:
            print('Error command')

        #accept()함수로 입력만 받아주고 이후 알고리즘은 핸들러에게 맡긴다.
        notice_thread = threading.Thread(target=handle_notice, args=(client_socket, addr, user))
        notice_thread.daemon = True
        notice_thread.start()

        receive_thread = threading.Thread(target=handle_receive, args=(client_socket, addr,user))
        receive_thread.daemon = True
        receive_thread.start()


if __name__ == '__main__':
    #parser와 관련된 메서드 정리된 블로그 : https://docs.python.org/ko/3/library/argparse.html
    #description - 인자 도움말 전에 표시할 텍스트 (기본값: none)
    #help - 인자가 하는 일에 대한 간단한 설명.
    parser = argparse.ArgumentParser(description="\nCho's server\n-p port\n")
    parser.add_argument('-p', help="port")

    args = parser.parse_args()
    try:
        port = int(args.p)
    except:
        pass
    accept_func()

