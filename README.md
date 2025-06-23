|   | **Share2Earn** - Earn passive income by sharing your spare Internet bandwidth through multiple services with an intuitive web UI. ⭐️ **Leave a star** if you like this project 🙂 |
| - | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

</p>

| <img src="./images/share2earn_logo.png" width="100" alt="Share2Earn Logo" /> | **Share2Earn** - Earn passive income by sharing your spare Internet bandwidth with a user-friendly web dashboard. ⭐️ **Star** this repo if you enjoy it! |
| :---------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------: |

## 🚀 Quick Start

Get up and running in a few simple steps:

1. 🛠️ **Prerequisites**

   * [Docker Engine](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
   * **Python 3.7+**

2. 📥 **Clone & Enter the Repo**

   ```bash
   git clone https://github.com/vanhbakaa/share2earn.git
   cd share2earn
   ```

3. 📦 **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. ▶️ **Launch the Dashboard**

   ```bash
   python main.py
   ```

   * Open your browser at [http://localhost:5000](http://localhost:5000).
   * First run auto-generates `data/` files and configurations.

---

## ⚙️ Configuration

All settings live under `data/` as JSON files:

| File                    | Purpose                                 |
| ----------------------- | --------------------------------------- |
| `dashboard_config.json` | Web UI port & admin credentials         |
| `app_config.json`       | Memory profiles & default apps          |
| `user_config.json`      | Your service accounts & global settings |

> 🔒 **Tip:** Update your admin username/password in `dashboard_config.json` before first use.

No extra environment variables needed. Ensure the `data/` folder is writable.

---

## 🖥️ Usage

1. 🔑 **Login:** Navigate to `http://localhost:5000` and sign in.
2. 🛠️ **Enable Apps:** Go to **Apps** / **Settings**, toggle services, and save your credentials.
3. 🚀 **Manage Containers:** In **Manage Containers**, Start/Stop each service—Docker images will download and run automatically.
4. 📊 **View Stats:** Check **Stats** for bandwidth usage and earnings.

> 💡 All actions are handled via the UI—no need for manual Docker commands.

---

## 🤝 Contributing

Contributions are warmly welcome!

* 🐛 Report issues or request features via GitHub Issues.
* 🍴 Fork the repo, create a branch, and submit a PR.
* 📐 Keep code style consistent and update this README for any new features.

---

## ⚖️ License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

> ⚠️ **Disclaimer:** Use at your own risk. Monitor your bandwidth and earnings when running multiple services.

---
