import os
import binascii
from random import SystemRandom
from typing import Tuple, List, Union
from base58 import b58encode_check, b58decode_check
from gmssl import sm2, sm3, func
from func import multiply

艾条密码消息 = "艾条密码".encode('utf-8')
艾条机ID消息 = "艾条机ID".encode('utf-8')
SK_PATH, PK_PATH = 'aijiu_secret_key.txt', 'aijiu_public_key.txt'
PK, SK = b'', b''
if os.path.isfile(SK_PATH):
    with open(SK_PATH, 'r') as f:
        SK = f.read().strip(' \n\t')
else:
    print('警告：没有找到公钥')
if os.path.isfile(PK_PATH):
    with open(PK_PATH, 'r') as f:
        PK = f.read().strip(' \n\t')
else:
    print('警告：没有找到公钥')
sm2_crypt = sm2.CryptSM2(SK, PK)


def gen_private_key(secret=None) -> str:
    n = int(sm2_crypt.ecc_table['n'], 16)
    secret = secret % n if secret else SystemRandom().randrange(1, n)
    return f"{secret:064x}"

def get_public_key(private_key: str) -> str:
    ecc_table = {k: int(v, 16) for k, v in sm2_crypt.ecc_table.items()}
    Gx = ecc_table['g'] >> 256
    Gy = ecc_table['g'] & ((0x1 << 256) - 1)
    xPublicKey, yPublicKey = multiply((Gx, Gy), int(private_key, 16), A=ecc_table['a'], P=ecc_table['p'], N=ecc_table['n'])
    return f"{xPublicKey:064x}{yPublicKey:064x}"

def gen_keypair_and_save(secret: Union[None, int] = None) -> Tuple[str, str]:
    sk = gen_private_key(secret)
    pk = get_public_key(sk)
    sm2_crypt = sm2.CryptSM2(sk, pk)
    for i in range(100):
        c = sm2_crypt.encrypt(艾条密码消息)
        assert sm2_crypt.decrypt(c) == 艾条密码消息
        sig = sm2_crypt.sign_with_sm3(艾条密码消息, func.random_hex(sm2_crypt.para_len))
        assert sm2_crypt.verify_with_sm3(sig, 艾条密码消息)
    if os.path.isfile(SK_PATH):
        raise FileExistsError('已生成过私钥')
    if os.path.isfile(PK_PATH):
        raise FileExistsError('已生成过公钥')
    with open(SK_PATH, 'w') as f:
        f.write(sk)
    with open(PK_PATH, 'w') as f:
        f.write(pk)
    return sk, pk

# TODO: 艾条密码生成方式未定
def sign_aitiao_passwd(count=100) -> List[Tuple[bytes, str]]:
    result = []
    for _ in range(count):
        sig = bytes.fromhex(sm2_crypt.sign_with_sm3(艾条密码消息, func.random_hex(sm2_crypt.para_len)))
        sm3_sig = sm3.sm3_hash(list(sig))
        result.append((sig, b58encode_check(bytes.fromhex(sm3_sig)).decode('utf-8')))
    return result

def verify_aitiao_passwd(passwd: Union[bytes, str]) -> bool:
    if type(passwd) is bytes:
        passwd = b58decode_check(passwd)
    return sm2_crypt.verify_with_sm3(passwd, 艾条密码消息)

def sign_client_id(count=100) -> List[bytes]:
    return [b58encode_check(bytes.fromhex(sm2_crypt.sign_with_sm3(艾条机ID消息, func.random_hex(sm2_crypt.para_len)))) for _ in range(count)]

def verify_client_id(client_id: Union[bytes, str]):
    if type(client_id) is bytes:
        client_id = b58decode_check(client_id)
    return sm2_crypt.verify_with_sm3(client_id, 艾条机ID消息)

if __name__ == '__main__':
    print(os.getcwd())
    print([i for i in sign_aitiao_passwd()])
    print(sign_client_id())
    gen_keypair_and_save()