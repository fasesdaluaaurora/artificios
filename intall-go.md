# Instalação do Go via Binário — Ubuntu 22.04 (amd64)

Referência: ambiente Ubuntu 22.04.3 LTS, arquitetura x86_64.

---

## 1. Pré-requisitos

```bash
# Verificar arquitetura da máquina
uname -m
# Saída esperada: x86_64

# Verificar versão do sistema
cat /etc/os-release | head -5
```

---

## 2. Baixar o binário oficial

Acesse https://go.dev/dl/ para conferir a versão mais recente.
A versão usada nesta VM é **go1.25.4**.

```bash
# Definir a versão desejada
GO_VERSION=1.25.4

# Baixar o tarball para a home do usuário
wget -P ~/ https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz
```

---

## 3. Extrair e instalar

```bash
# Criar o diretório de instalação (dentro do home do usuário, sem precisar de sudo)
mkdir -p ~/.local/go${GO_VERSION}

# Extrair o tarball
tar -C ~/.local/go${GO_VERSION} --strip-components=1 -xzf ~/go${GO_VERSION}.linux-amd64.tar.gz

# Criar um symlink para facilitar atualizações futuras
ln -sfn ~/.local/go${GO_VERSION} ~/.local/go

# Verificar os binários extraídos
ls ~/.local/go/bin/
# Saída esperada: go  gofmt
```

---

## 4. Configurar o PATH

Adicione as linhas abaixo ao final do `~/.bashrc`:

```bash
# Abre o arquivo para edição
nano ~/.bashrc
```

Conteúdo a adicionar:

```bash
# Go
export PATH="$PATH:$HOME/.local/go/bin"
```

Recarregue o shell:

```bash
source ~/.bashrc
```

---

## 5. Verificar a instalação

```bash
go version
# Saída esperada: go version go1.25.4 linux/amd64

which go
# Saída esperada: /home/<usuario>/.local/go/bin/go

go env GOROOT
# Saída esperada: /home/<usuario>/.local/go1.25.4
```

---

## 6. (Opcional) Configurar GOPATH

Por padrão o Go usa `~/go` como GOPATH. Se quiser um caminho diferente:

```bash
# Adicionar ao ~/.bashrc
export GOPATH="$HOME/projetos/go"
export PATH="$PATH:$GOPATH/bin"
```

---

## 7. Remover a versão antiga (atualização)

Para trocar de versão sem perder a instalação atual:

```bash
GO_NEW=1.25.4

# Baixar e instalar no novo diretório
wget -P ~/ https://go.dev/dl/go${GO_NEW}.linux-amd64.tar.gz
mkdir -p ~/.local/go${GO_NEW}
tar -C ~/.local/go${GO_NEW} --strip-components=1 -xzf ~/go${GO_NEW}.linux-amd64.tar.gz

# Redirecionar o symlink
ln -sfn ~/.local/go${GO_NEW} ~/.local/go

# Confirmar
go version
```

O diretório antigo continua em `~/.local/goX.Y.Z` e pode ser removido quando não for mais necessário:

```bash
rm -rf ~/.local/go1.24.x
```

---

## Resumo dos diretórios

| Diretório | Descrição |
|---|---|
| `~/.local/go<versao>/` | Binário do Go extraído |
| `~/.local/go/` | Symlink apontando para a versão ativa |
| `~/.local/go/bin/` | Executáveis `go` e `gofmt` |
| `~/go/` | GOPATH padrão (módulos baixados via `go get`) |
