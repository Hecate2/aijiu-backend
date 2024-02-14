import os
import binascii
from typing import Tuple, List, Union
from base58 import b58encode_check, b58decode_check
from gmssl import sm2, sm3, utils

艾条密码消息 = "艾条密码".encode('utf-8')
艾条机ID消息 = "艾条机ID".encode('utf-8')
SK_PATH, PK_PATH = 'aijiu_secret_key.txt', 'aijiu_public_key.txt'
PK, SK = b'', b''
if os.path.isfile(SK_PATH):
    with open(SK_PATH, 'r') as f:
        SK = bytes.fromhex(f.read())
else:
    print('警告：没有找到公钥')
if os.path.isfile(PK_PATH):
    with open(PK_PATH, 'r') as f:
        PK = bytes.fromhex(f.read())
else:
    print('警告：没有找到公钥')
sm2_crypt = sm2.SM2Crypt()
if PK and SK:
    sm2_crypt.set_key_pair(SK, PK)

def gen_keypair_and_save(secret: Union[None, int] = None) -> Tuple[bytes, bytes]:
    sk, pk = sm2_crypt.gen_key_pair(secret)
    sm2_crypt.set_key_pair(sk, pk)
    for i in range(100):
        c = sm2_crypt.encrypt(艾条密码消息)
        assert sm2_crypt.decrypt(binascii.unhexlify(c)) == 艾条密码消息
        sig = sm2_crypt.sign_with_sm3(艾条密码消息, utils.random_hex(sm2_crypt.para_len))
        assert sm2_crypt.verify_with_sm3(sig, 艾条密码消息)
    if os.path.isfile(SK_PATH):
        raise FileExistsError('已生成过私钥')
    if os.path.isfile(PK_PATH):
        raise FileExistsError('已生成过公钥')
    with open(SK_PATH, 'w') as f:
        f.write(sk.hex())
    with open(PK_PATH, 'w') as f:
        f.write(pk.hex())
    return sk, pk

# TODO: 艾条密码生成方式未定
def sign_aitiao_passwd(count=100) -> List[Tuple[bytes, str]]:
    result = []
    for _ in range(count):
        sig = bytes.fromhex(sm2_crypt.sign_with_sm3(艾条密码消息, utils.random_hex(sm2_crypt.para_len)).decode())
        sm3_sig = bytes.fromhex(sm3.sm3_hash(sig).decode())
        result.append((sig, b58encode_check(sm3_sig).decode('utf-8')))
    return result

def verify_aitiao_passwd(passwd: Union[bytes, str]) -> bool:
    if type(passwd) is bytes:
        passwd = b58decode_check(passwd)
    return sm2_crypt.verify_with_sm3(passwd, 艾条密码消息)

def sign_client_id(count=100) -> List[bytes]:
    return [b58encode_check(bytes.fromhex(sm2_crypt.sign_with_sm3(艾条机ID消息, utils.random_hex(sm2_crypt.para_len)).decode())) for _ in range(count)]

def verify_client_id(client_id: Union[bytes, str]):
    if type(client_id) is bytes:
        client_id = b58decode_check(client_id)
    return sm2_crypt.verify_with_sm3(client_id, 艾条机ID消息)

if __name__ == '__main__':
    print(os.getcwd())
    print([i for i in sign_aitiao_passwd()])
    print(sign_client_id())
    gen_keypair_and_save()