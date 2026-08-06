// Service Worker do Kairos Igreja v2
// Mudanca: HTML nunca vai pro cache (sempre network-first)
const CACHE = "kairos-igreja-v2";
const STATIC_ASSETS = [
  "/manifest.json",
  "/icon-192.png",
  "/icon-512.png",
  "/icon-maskable-512.png",
  "/apple-touch-icon.png",
  "/favicon.ico",
];

self.addEventListener("install", (event) => {
  // Ativa a nova versao imediatamente
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    Promise.all([
      // Limpa TODOS os caches antigos (v1, etc)
      caches.keys().then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      ),
      // Cacheia assets estaticos
      caches.open(CACHE).then((cache) => cache.addAll(STATIC_ASSETS).catch(() => {})),
    ])
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // NUNCA cacheia API
  if (url.pathname.startsWith("/api/")) {
    return;
  }

  // Paginas HTML: SEMPRE vem da rede (nunca cache)
  const accept = event.request.headers.get("accept") || "";
  if (event.request.method === "GET" && accept.includes("text/html")) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match("/"))
    );
    return;
  }

  // Outros assets: tenta rede, fallback pro cache
  if (event.request.method === "GET") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok && url.origin === location.origin) {
            const clone = response.clone();
            caches.open(CACHE).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
  }
});
