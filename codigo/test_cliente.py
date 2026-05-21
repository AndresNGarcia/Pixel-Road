from red.cliente import Cliente

cliente = Cliente()

ip = input(
    "Ingresa IP del host: "
)

cliente.conectar(ip)

while True:
    mensaje = input("Tu mensaje: ")

    cliente.enviar(mensaje)

    respuesta = cliente.recibir()

    print(
        "Servidor:",
        respuesta
    )