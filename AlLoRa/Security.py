try:
    import ucryptolib as cryptolib
    import uos as os
    import ubinascii as binascii
    from cryptography import ciphers
    Cipher = ciphers.Cipher
    algorithms = ciphers.algorithms
    modes = ciphers.modes
    AESGCM = ciphers.AESGCM

except ImportError:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
    import os
    import base64 as binascii


class Security:
    def __init__(self):
        # self.password = password.encode()
        # self.salt = salt if salt else os.urandom(16)  # Use a random salt if none is provided
        # self.AppEUI = AppEUI
        # self.DevEUI = DevEUI
        # self.AppNonce = AppNonce
        self.AppKey = b'\xd1}\x9c"e\x0c\xe0\xafb\x1c\xf3J^\xd7\xa7y<\x17\xdd\xed`eD\x051\xae\xbb\xa2\x91\xfeD\xe1'  # 16 bytes
        self.nonce = b"7M\xb4xy\x01t\x88\xd8\xf3\x9e\xc0"  # 12 bytes Nonce that is an initialization vector and provides randomness
        self.aad = b"\xDE\xAD\xBE\xEF"  # Additional Authenticated Data

    def aesgcm_encrypt(self, payload):
        cipher = Cipher(algorithms.AES(self.AppKey), modes.GCM(self.nonce))
        encryptor = cipher.encryptor()
        encryptor.authenticate_additional_data(self.aad)
        ct = encryptor.update(payload) + encryptor.finalize()

        tag = encryptor.tag
        tag_length = 3
        truncated_tag = tag[:tag_length]

        encrypted_payload = ct + truncated_tag
        return encrypted_payload, truncated_tag

    def aesgcm_decrypt(self, encrypted_payload):
        if not encrypted_payload:
            return encrypted_payload
        else:
            truncated_tag = encrypted_payload[-3:]  # Get the last 4 bytes of the encrypted payload
            cipher = Cipher(algorithms.AES(self.AppKey), modes.GCM(self.nonce, tag=truncated_tag))
            decryptor = cipher.decryptor()
            decryptor.authenticate_additional_data(self.aad)
            dt = decryptor.update(encrypted_payload[:-3]) + decryptor.finalize() # Decrypt the encrypted payload without the last 4 bytes
            # print(dt)
        return dt
    '''
    def encrypt(self, plaintext):
        # Use AES128 to encrypt the plaintext
        key = self.password
        iv = os.urandom(16)
        cipher = cryptolib.aes(key, 1, iv)
        ciphertext = cipher.encrypt(plaintext.encode())
        return binascii.b2a_base64(iv + ciphertext)

    def decrypt(self, ciphertext):
        # Decrypt the ciphertext with AES128
        key = self.password
        ciphertext = binascii.a2b_base64(ciphertext)
        iv = ciphertext[:16]
        ciphertext = ciphertext[16:]
        cipher = cryptolib.aes(key, 0, iv)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext.decode()
    '''
    '''
    def send_parameters(self, node: Node):
        # Generate parameters
        AppEUI, DevEUI, AppNonce = self.generate_parameters()

        # Create a packet with the parameters
        packet_content = {"AppEUI": AppEUI, "DevEUI": DevEUI, "AppNonce": AppNonce}
        packet = Packet(content=dumps(packet_content))

        # Send the packet to the node
        node.receive_parameters(packet)

    def receive_parameters(self, packet: Packet):
        # Get the content of the packet
        content = packet.get_content()

        # Decrypt the content
        decrypted_content = self.security.decrypt(content)

        # Load the parameters from the decrypted content
        parameters = loads(decrypted_content)

        # Set the parameters
        self.AppEUI = parameters["AppEUI"]
        self.DevEUI = parameters["DevEUI"]
        self.AppNonce = parameters["AppNonce"]
    '''


