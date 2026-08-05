# Kairos Igreja — Frontend (Next.js PWA)

## Instalação

```bash
cd frontend
npm install
```

## Desenvolvimento

Certifique-se de que o backend está rodando em http://localhost:8000

```bash
npm run dev
```

Acesse: http://localhost:3000

No celular (mesma rede Wi-Fi):
1. Descubra o IP do computador (`ipconfig` no Windows ou `hostname -I` no Linux)
2. Acesse `http://SEU_IP:3000`
3. No Chrome/Safari, adicione à tela inicial para usar como PWA

## Variável de ambiente (opcional)

Crie `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Para acesso pelo celular na rede, use o IP:
```
NEXT_PUBLIC_API_URL=http://192.168.x.x:8000/api
```
