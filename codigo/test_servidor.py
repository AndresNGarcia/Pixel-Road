from red.servidor import Servidor

server = Servidor()

server.iniciar()

while True:
    msg = server.recibir()

    print("Cliente:", msg)

    server.enviar(
        "Mensaje recibido"
    )