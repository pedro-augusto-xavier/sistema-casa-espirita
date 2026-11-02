"""Regras de senha forte -- valem pra senha que a própria pessoa escolhe.

A senha que um admin define no cadastro (ex: os 8 números do CPF) é só
provisória: no primeiro acesso a pessoa é obrigada a trocar, e aí estas
regras entram.

Seguimos a linha do NIST (SP 800-63B): tamanho mínimo decente, recusar
senhas manjadas e coisas óbvias do contexto (nome da pessoa, nome da casa),
sem exigir "uma maiúscula, um símbolo..." -- isso só gera senha difícil de
lembrar e fácil de adivinhar.
"""

import unicodedata

TAMANHO_MINIMO = 10
TAMANHO_MAXIMO = 128

# As mais usadas no Brasil e no mundo (listas públicas de vazamentos),
# já em minúsculas. Não precisa ser enorme: o limite de tentativas cuida
# do resto.
_COMUNS = {
    "1234567890", "0123456789", "12345678910", "1234567891", "0987654321",
    "1111111111", "0000000000", "1122334455", "1212121212", "1020304050",
    "123123123123", "123456789a", "a123456789", "abc1234567", "abcd123456",
    "qwertyuiop", "qwerty1234", "qwerty123456", "asdfghjkl1", "zxcvbnm123",
    "1q2w3e4r5t", "1qaz2wsx3edc", "q1w2e3r4t5", "password1", "password123",
    "password12", "passw0rd123", "iloveyou12", "senha12345", "senha123456",
    "minhasenha", "minhasenha1", "minhasenha123", "senhasenha", "senhaforte",
    "senhaforte1", "senhaforte123", "mudar12345", "mudar123456", "trocar1234",
    "trocar123456", "alterar123", "brasil1234", "brasil123456", "flamengo123",
    "flamengo1234", "vasco12345", "botafogo123", "fluminense1", "corinthians",
    "corinthians1", "palmeiras1", "palmeiras123", "saopaulo123", "gremio12345",
    "deusefiel", "deusefiel1", "deusefiel123", "jesuscristo", "jesusteama",
    "jesus12345", "jesus123456", "deus123456", "deusmeama", "gratidao123",
    "familia123", "familia1234", "amor123456", "teamo12345", "teamo123456",
    "princesa123", "princesa1234", "estrela123", "felicidade", "felicidade1",
    "saudade123", "esperanca1", "abcdefghij", "administrador", "admin12345",
    "admin123456", "administrator", "usuario123", "usuario1234", "welcome123",
    "sunshine12", "football12", "baseball12", "superman12", "batman12345",
    "dragon1234", "monkey1234", "master1234", "letmein123", "trustno1234",
}

# Palavras do próprio contexto: quem tentar adivinhar começa por elas.
_PALAVRAS_DO_CONTEXTO = (
    "amoreperdao",
    "amorperdao",
    "casaespirita",
    "espirita",
    "friburgo",
    "allankardec",
    "kardec",
    "chicoxavier",
)


def _normaliza(texto: str) -> str:
    """minúsculas, sem acento, só letras e números."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acento.lower() if c.isalnum())


def problema_da_senha(senha: str, *, nome: str | None = None) -> str | None:
    """Devolve a explicação do problema, ou None se a senha está boa."""
    if len(senha) < TAMANHO_MINIMO:
        return f"A senha precisa ter pelo menos {TAMANHO_MINIMO} caracteres."
    if len(senha) > TAMANHO_MAXIMO:
        return f"A senha pode ter no máximo {TAMANHO_MAXIMO} caracteres."

    normalizada = _normaliza(senha)
    if senha.lower() in _COMUNS or normalizada in _COMUNS:
        return "Essa senha é muito usada e fácil de adivinhar. Escolha outra."
    if len(set(senha)) <= 2:
        return "A senha não pode ser um caractere repetido."
    if normalizada.isdigit():
        # CPF, telefone, data de nascimento... tudo isso é número que
        # alguém pode descobrir.
        return (
            "Use pelo menos uma letra -- só números (CPF, telefone, data) "
            "é fácil de descobrir."
        )
    for palavra in _PALAVRAS_DO_CONTEXTO:
        if palavra in normalizada:
            return "Não use o nome da casa ou palavras ligadas a ela na senha."
    if nome:
        for parte in nome.split():
            parte_normalizada = _normaliza(parte)
            if len(parte_normalizada) >= 4 and parte_normalizada in normalizada:
                return "Não use o seu nome na senha."
    return None
