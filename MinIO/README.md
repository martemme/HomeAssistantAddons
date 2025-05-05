# MinIO Add-on per Home Assistant

Questo add-on fornisce un server **S3 compatibile** basato su MinIO, perfetto per:

- Backup di **Longhorn**
- Archiviazione file/media
- Logging o integrazioni custom

È stato progettato per essere **production-ready**, sicuro, leggero e accessibile direttamente via pannello laterale di Home Assistant.

## ⚙️ Configurazione

```yaml
access_key: admin
secret_key: CHANGEME-strong-password
region: us-east-1
bucket: longhorn-backup
```

## 🌐 Accesso

Una volta installato, accedi a MinIO tramite il pannello laterale o all'indirizzo:

`http://<ip_hass>:9000` (se Ingress non è disponibile)

## 🚀 Installazione

1. Vai su Home Assistant → **Supervisor → Add-on Store**
2. Aggiungi la tua repo Git custom (Settings → Repositories → `https://github.com/<tuo-utente>/minio-addon`)
3. Installa l’add-on, avvia e accedi a MinIO via Ingress

## 🧾 Requisiti

- Home Assistant OS o Supervised
- Architettura supportata: `amd64`, `aarch64`
- Accesso a una cartella persistente per `/data`

## 📂 Struttura del repository

```bash
minio-addon/
├── config.json         # Definizione dell’add-on
├── Dockerfile          # Contenitore MinIO
├── run.sh              # Entrypoint con supporto TLS e bucket auto-creation
├── README.md
└── ...
```

## 🧠 Note
Il bucket specificato in bucket: viene creato automaticamente se non esiste

Se usi Longhorn, puoi puntare i backup a:

```bash
http://<IP_HASS>:9000/longhorn-backup
```
Le credenziali vengono passate come variabili d'ambiente in fase di bootstrap

## 🛡 Sicurezza
> ⚠️ Usa sempre password forti.

Considera l’attivazione del TLS automatico posizionando i certificati in `/ssl/`.

## ✅ TODO futuri
- Supporto per versioning bucket
- Healthcheck e metriche Prometheus
- Interfaccia per gestione utenti/bucket via opzioni

---
Realizzato con ❤️ per l’automazione e la resilienza.