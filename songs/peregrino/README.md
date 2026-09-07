# Peregrino (CD2) — Amarílio Fontenele

Letras oficiais do novo álbum, extraídas de
`assets/references/CD2 PEREGRINO as Letras.pdf` (fonte da verdade) e já
convertidas de caixa-alta para o formato usado nos `.lrc` finais. Cada
arquivo tem um cabeçalho com título, tom e uma lista **"Conferir com a
gravação"** apontando prováveis erros de digitação do PDF — sempre
resolver ouvindo o áudio.

## Faixas

| # | Faixa | Tom | Arquivo |
|---|-------|-----|---------|
| 1 | Ah Você! (partes I e II) | D / C | `01-ah-voce.txt` |
| 2 | Bom Conselho | G | `02-bom-conselho.txt` |
| 3 | Certeza das Certezas | Dm | `03-certeza-das-certezas.txt` |
| 4 | Pelo Chão | C | `04-pelo-chao.txt` |
| 5 | Consuma com Sumo Cuidado | F | `05-consuma-com-sumo-cuidado.txt` |
| 6 | Minha Veia de Poeta | Em | `06-minha-veia-de-poeta.txt` |
| 7 | Mas Eu Prefiro Crer | Cm | `07-mas-eu-prefiro-crer.txt` |
| 8 | Luz Rebrilhante | D | `08-luz-rebrilhante.txt` |
| 9 | Nicodemos | G | `09-nicodemos.txt` |
| 10 | Peregrino (faixa-título) | Em | `10-peregrino.txt` |
| 11 | Como Agradecer? | B | `11-como-agradecer.txt` |
| 12 | Finalmente, Irmãos | A | `12-finalmente-irmaos.txt` |
| 13 | Samba Enredo do Cristão | C | `13-samba-enredo-do-cristao.txt` |

## Status

- **Áudios**: chegaram 2026-09-07 no branch
  `claude/lyrics-videos-project-cx2e7p` (13 MP3s "NN TÍTULO.mp3" na raiz
  do repositório; os nomes usam Unicode decomposto — usar glob no shell).
- **Letras cronometradas**: prontas — `songs/<slug>.raw.lrc` (âncoras da
  transcrição) e `songs/<slug>.lrc` (final, letra oficial sobre as
  âncoras) para as 13 faixas. Trechos que o VAD perdia foram
  re-transcritos em clipes com +9dB (padrão do projeto). Vários typos do
  PDF foram resolvidos de ouvido (ver os cabeçalhos "Resolvido na
  gravação" nos .txt).

## O que ainda falta para produzir os vídeos

1. **Arte do álbum como arquivo** — a capa (título azul "PEREGRINO" +
   faixa preta com "Amarilio Fontenele" em dourado sobre ondas de papel
   branco) e o fundo (ondas de papel branco) foram mostrados no chat,
   mas não vieram como arquivos. Salvar em
   `assets/albums/peregrino/cover.png` e `assets/albums/peregrino/bg.png`.
2. **Brand** — criar `brands/peregrino.json` depois que as imagens
   existirem (o carregador de brand exige que os arquivos existam).
   Paleta sugerida pela capa: fundo claro de papel, azuis
   (~`#29abe2` claro / `#1b3fa0` escuro), dourado `#e0a63c`, preto da
   faixa — ou seja, um brand de fundo claro no estilo do
   `brands/simplesmente-graca.json` (texto escuro sobre bloco claro).
