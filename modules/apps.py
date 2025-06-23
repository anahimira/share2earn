apps = [
    {
        "id": "mysterium",
        "name": "Mysterium Node",
        "description": "Run a decentralized VPN node and earn crypto.",
        "instructions": """
            1. Register an account at <a href="https://mystnodes.com/?referral_code=pWOQ1NHsR6gDndMAlSR58QweMfnIjFf8dkKvbyCP" target="_blank">Mysterium Nodes</a>.<br>
            2. Choose a port for the local dashboard (e.g., 4449). After running, access the local dashboard at <code>127.0.0.1:{dashboard_port}</code> to monitor your node.<br>
        """,
        "docker_image": "mysteriumnetwork/myst:latest",
        "config_fields": ["dashboard_port"],
        "port_mappings": {"4449": "dashboard_port"},
        "volume_mounts": ["./mysterium-data:/var/lib/mysterium-node"],
        "command": "service --agreed-terms-and-conditions",
        "capabilities": ["NET_ADMIN"],
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto",
        "claim_info": "Visit <a href='http://localhost:{dashboard_port}' target='_blank'>http://localhost:{dashboard_port}</a> to claim and manage your node."
    },
    {
        "id": "honeygain",
        "name": "Honeygain",
        "description": "Earn rewards by sharing your internet bandwidth.",
        "instructions": """
            1. Register an account at <a href="https://r.honeygain.me/VANHB378B6" target="_blank">Honeygain</a>.<br>
            2. Enter your Honeygain email and password here.
        """,
        "docker_image": "honeygain/honeygain",
        "config_fields": ["email", "password"],
        "auto_set_cmd": ["device_name"],
        "config_type": "command",
        "max_devices_per_account": 10,
        "devices_per_ip": 1,
        "payment": "Crypto, Paypal",
        "command_template": "-tou-accept -email {email} -pass {password} -device {device_name}",
        "supports_proxy": True
    },
    {
        "id": "pawns",
        "name": "Pawns",
        "description": "Earn rewards by sharing your internet bandwidth.",
        "instructions": """
            1. Register an account at <a href="https://pawns.app/?r=14062031" target="_blank">Pawns.app</a>.<br>
            2. Enter your Pawns email and password here.
        """,
        "docker_image": "iproyal/pawns-cli:latest",
        "config_fields": ["email", "password"],
        "auto_set_cmd": ["device_name", "device_id"],
        "config_type": "command",
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto, Paypal",
        "command_template": "-email={email} -password={password} -device-name={device_name} -device-id={device_id} -accept-tos",
        "supports_proxy": True
    },
    {
        "id": "earnapp",
        "name": "EarnApp",
        "description": "Earn money by sharing your internet connection.",
        "instructions": """
            1. Register for EarnApp at <a href="https://earnapp.com/i/mF4t9Bhy" target="_blank">EarnApp</a><br>
            2. you can generate a random UUID by clicking "Generate Random UUID" or use a registered UUID.<br>
            3. Enter your UUID here and save the configuration.
        """,
        "docker_image": "fazalfarhan01/earnapp:lite",
        "config_fields": ["uuid"],
        "config_type": "environment",
        "environment_map": {"EARNAPP_UUID": "uuid", "EARNAPP_TERM": "term"},
        "volume_mounts": ["./earnapp-data:/etc/earnapp"],
        "max_devices_per_account": "10",
        "devices_per_ip": 1,
        "payment": "Paypal, Gift Card",
        "claim_info": "Visit <a href='https://earnapp.com/r/sdk-node-{uuid}' target='_blank'>https://earnapp.com/r/sdk-node-{uuid}</a> to claim your node.",
        "supports_proxy": True
    },
    {
        "id": "packetstream",
        "name": "PacketStream",
        "description": "Earn rewards by sharing your internet bandwidth with PacketStream's residential proxy network.",
        "instructions": """
            1. Register an account at <a href="https://packetstream.io/?psr=79qJ" target="_blank">PacketStream</a>.<br>
            2. After logging in, navigate to the Download page.<br>
            3. Scroll to the bottom of the page where the Linux setup instructions are provided.<br>
            4. In those instructions, you will find your unique CID (Client ID).<br>
            5. Enter your CID in the configuration field below.
        """,
        "docker_image": "packetstream/psclient:latest",
        "config_fields": ["cid"],
        "config_type": "environment",
        "environment_map": {"CID": "cid"},
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Paypal",
        "supports_proxy": True
    },
    {
        "id": "traffmonetizer",
        "name": "TraffMonetizer",
        "description": "Earn money by sharing your internet connection with TraffMonetizer.",
        "instructions": """
            1. Sign up at <a href="https://shorturl.at/Byyk1" target="_blank">TraffMonetizer</a> <br>
            2. Log in to your dashboard at <a href="https://app.traffmonetizer.com/dashboard" target="_blank">TraffMonetizer Dashboard</a>.<br>
            3. Find your unique token on the dashboard (usually in the upper left corner or settings).<br>
            4. Enter this token in the configuration field below.
        """,
        "docker_image": "traffmonetizer/cli_v2:latest",
        "config_fields": ["token"],
        "config_type": "command",
        "auto_set_cmd": ["device_name"],
        "command_template": "start accept --token {token} --device-name {device_name}",
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": "Unlimited",
        "payment": "Crypto",
        "supports_proxy": True,
        "supports_datacenter_ip": True

    },
    {
        "id": "earnfm",
        "name": "EarnFM",
        "description": "Generate passive income by sharing your internet bandwidth with EarnFM.",
        "instructions": """
            1. Sign up at <a href="https://earn.fm/ref/VANH75DS" target="_blank">EarnFM</a> to get 5$.<br>
            2. Log in to your dashboard at <a href="https://app.earn.fm/" target="_blank">EarnFM Dashboard</a>.<br>
            3. Navigate to the settings or API section to find your unique API key.<br>
            4. Enter the API key in the configuration field below.
        """,
        "docker_image": "earnfm/earnfm-client:latest",
        "config_fields": ["apikey"],
        "config_type": "environment",
        "environment_map": {"EARNFM_TOKEN": "apikey"},
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto, Paypal, Giftcard",
        "supports_proxy": True,
        "supports_datacenter_ip": True
    },
    {
        "id": "repocket",
        "name": "Repocket",
        "description": "Earn passive income by sharing your unused internet bandwidth with Repocket.",
        "instructions": """
            1. Sign up at <a href="https://link.repocket.com/7585 target="_blank">Repocket</a>Use your email to register.<br>
            2. Log in to your dashboard at <a href="https://link.repocket.com/7585 target="_blank">Repocket Dashboard</a>.<br>
            3. Navigate to the share internet section to find your unique API key.<br>
            4. Enter your email and API key in the configuration fields below.
        """,
        "docker_image": "repocket/repocket:latest",
        "config_fields": ["email", "apikey"],
        "config_type": "environment",
        "environment_map": {"RP_EMAIL": "email", "RP_API_KEY": "apikey"},
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 2,
        "payment": "Paypal, Wise, Crypto",
        "supports_proxy": True,
        "supports_datacenter_ip": True
    },
    {
        "id": "bitping",
        "name": "Bitping",
        "description": "Earn passive income by running a Bitping node to share your internet bandwidth.",
        "instructions": """
            1. Register an account at <a href="https://app.bitping.com/register target="_blank">Bitping</a>.<br>
            2. Enter your email, password, and 2FA code in the configuration fields below.
        """,
        "docker_image": "bitping/bitpingd:latest",
        "config_fields": ["email", "password", "mfa"],
        "config_type": "environment",
        "environment_map": {"BITPING_EMAIL": "email", "BITPING_PASSWORD": "password", "BITPING_MFA": "mfa"},
        "volume_mounts": [".data/.bitpingd:/root/.bitpingd"],
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto",
        "supports_proxy": True,
        "supports_datacenter_ip": True
    },
    {
        "id": "proxylite",
        "name": "Proxylite",
        "description": "Earn passive income by sharing your internet bandwidth with Proxylite.",
        "instructions": """
            1. Register an account at <a href="https://proxylite.ru/?r=RRVJAXEV" target="_blank">Proxylite</a><br>
            2. After signing up, log in to your dashboard at <a href="https://lk.proxylite.ru/index.php" target="_blank">Proxylite Dashboard</a>.<br>
            3. Find your unique User ID.<br>
            4. Enter your User ID in the configuration field below.
        """,
        "docker_image": "proxylite/proxyservice:latest",
        "config_fields": ["userid"],
        "config_type": "environment",
        "environment_map": {"USER_ID": "userid"},
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto",
        "supports_proxy": True,
        "supports_datacenter_ip": True
    },
    {
        "id": "proxyrack",
        "name": "ProxyRack",
        "description": "Earn passive income by running a ProxyRack node to share your internet bandwidth.",
        "instructions": """
            1. Register an account at <a href="https://peer.proxyrack.com/ref/tehldaatzllsgrjcjrwm2srkdq7mawr5exstzqad" target="_blank">ProxyRack</a><br>
            2. Log in to your dashboard at <a href="https://peer.proxyrack.com/dashboard" target="_blank">ProxyRack Dashboard</a>.<br>
            3. Find your API key in API section.<br>
            4. Generate a random UUID using the button below or enter a custom one.<br>
            5. Enter your API key and UUID in the configuration fields below.
        """,
        "docker_image": "proxyrack/pop:latest",
        "config_fields": ["apikey", "uuid"],
        "config_type": "environment",
        "environment_map": {"api_key": "apikey", "UUID": "uuid"},
        "max_devices_per_account": 500,
        "devices_per_ip": 1,
        "payment": "Paypal",
        "claim_info": "After starting the app, add your node in the ProxyRack dashboard's device page using the UUID.",
        "supports_proxy": True,
        "supports_datacenter_ip": True
    },
    {
        "id": "packetshare",
        "name": "Packetshare",
        "description": "Earn passive income by sharing your internet bandwidth with Packetshare.",
        "instructions": """
            1. Register an account at <a href="https://www.packetshare.io/?code=168AE5B74053D709" target="_blank">Packetshare</a> using the referral link.<br>
            2. Log in to your dashboard at <a href="https://packetshare.io/ucenter.html" target="_blank">Packetshare Dashboard</a>.<br>
            3. Enter your registered email and password in the configuration fields below.
        """,
        "docker_image": "packetshare/packetshare:latest",
        "config_fields": ["email", "password"],
        "config_type": "command",
        "command_template": "-accept-tos -email={email} -password={password}",
        "max_devices_per_account": "10",
        "devices_per_ip": 1,
        "payment": "Paypal",
        "supports_proxy": True
    },
    {
        "id": "gaganode",
        "name": "GaGaNode",
        "description": "Earn passive income by sharing your internet bandwidth with GaGaNode's decentralized marketplace.",
        "instructions": """
            1. Register an account at <a href="https://dashboard.gaganode.com/register" target="_blank">GaGaNode</a>.<br>
            2. Log in to your dashboard at <a href="https://dashboard.gaganode.com" target="_blank">GaGaNode Dashboard</a>.<br>
            3. Find your unique token in your account settings or node setup section.<br>
            4. Enter your token in the configuration field below.
        """,
        "docker_image": "xterna/gaga-node:latest",
        "config_fields": ["token"],
        "config_type": "environment",
        "environment_map": {"TOKEN": "token"},
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto",
        "supports_proxy": True,
        "supports_datacenter_ip": True
    },
    {
        "id": "peer2profit",
        "name": "Peer2Profit",
        "description": "Earn passive income by sharing your internet bandwidth with Peer2Profit.",
        "instructions": """
            1. Register an account via Telegram at <a href="https://t.me/peer2profit_app_bot" target="_blank">Peer2Profit Bot</a>.<br>
            2. Log in to your dashboard using the same Telegram bot at <a href="https://t.me/peer2profit_app_bot" target="_blank">Peer2Profit Dashboard</a>.<br>
            3. Note your registered email address used with the Telegram bot.<br>
            4. Enter your email in the configuration field below.
        """,
        "docker_image": "enwaiax/peer2profit:latest",
        "config_fields": ["email"],
        "config_type": "environment",
        "environment_map": {"email": "email"},
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": "Unlimited",
        "payment": "Crypto",
        "supports_proxy": True,
        "supports_datacenter_ip": True
    },
    {
        "id": "depin_node",
        "name": "Depin Node",
        "description": "Run decentralized nodes (Grass, Gradient, Dawn, Teno, NodePay) to earn rewards by sharing resources.",
        "sub_apps": [
            {
                "id": "grass",
                "name": "Grass",
                "instructions": """
                    1. Sign up at <a href="https://app.grass.io/register/?referralCode=QYG4nXpdiwzpUeh" target="_blank">Grass</a> using your email.<br>
                    2. Log in to your Grass dashboard to verify your account.<br>
                    3. Enter your Grass email and password in the configuration fields below.<br>
                    4. Save the configuration and run the app to start earning rewards.
                """,
                "config_fields": ["grass_user", "grass_pass"],
                "environment_map": {"GRASS_USER": "grass_user", "GRASS_PASS": "grass_pass"}
            },
            {
                "id": "gradient",
                "name": "GradientNode",
                "instructions": """
                    1. Register at <a href="https://app.gradient.network/signup?code=EPITT6" target="_blank">Gradient Network</a> with your email.<br>
                    2. Verify your account via the Gradient dashboard.<br>
                    3. Enter your Gradient email and password in the configuration fields below.<br>
                    4. Save and run the app to connect your node to the Gradient network.
                """,
                "config_fields": ["gradient_email", "gradient_pass"],
                "environment_map": {"GRADIENT_EMAIL": "gradient_email", "GRADIENT_PASS": "gradient_pass"}
            },
            {
                "id": "dawn",
                "name": "Dawn",
                "instructions": """
                    1. Sign up at <a href="https://dashboard.dawninternet.com/signup?code=924m8xiq" target="_blank">Dawn</a> using your email and ref code: <code>924m8xiq</code>.<br>
                    2. Enter your Dawn email and password in the configuration fields below.<br>
                    3. Save the configuration and start the app to begin sharing resources.
                """,
                "config_fields": ["dawn_email", "dawn_pass"],
                "environment_map": {"DAWN_EMAIL": "dawn_email", "DAWN_PASS": "dawn_pass"}
            },
            {
                "id": "teno",
                "name": "Teneo",
                "instructions": """
                    1. Register at <a href="https://dashboard.teneo.pro/auth/signup?referralCode=TYCUc" target="_blank">Teneo Network</a>.<br>
                    2. Follow the setup guide on <a href="https://github.com/Masterofnoothing/DockWeb/blob/master/Instructions/teneo.md" target="_blank">github</a> to obtain your cookie value.<br>
                    3. Enter the Teneo cookie in the configuration field below.<br>
                    4. Save and run the app to activate your Teno node.
                """,
                "config_fields": ["teno_cookie"],
                "environment_map": {"TENO_COOKIE": "teno_cookie"}
            },
            {
                "id": "nodepay",
                "name": "NodePay",
                "instructions": """
                    1. Sign up at <a href="https://app.nodepay.ai/register?ref=xu2nKX1nC4V3KMN" target="_blank">NodePay</a>.<br>
                    2. Follow the setup guide on <a href="https://github.com/Masterofnoothing/DockWeb/blob/master/Instructions/nodepay.md" target="_blank">github</a> to obtain your cookie value.<br>
                    3. Enter the NodePay cookie in the configuration field below.<br>
                    4. Save and run the app to start earning with NodePay.
                """,
                "config_fields": ["np_cookie"],
                "environment_map": {"NP_COOKIE": "np_cookie"}
            }
        ],
        "docker_image": "carbon2029/dockweb",
        "config_type": "environment",
        "volume_mounts": ["./chrome_user_data:/app/chrome_user_data"],
        "port_mappings": {"8000": "8000"},
        "restart_policy": "unless-stopped",
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto",
        "claim_info": "Note: If you run all 5 apps, ensure you have selected a sufficient memory profile (it will consume about 500MB-1GB if you run all 5 apps)."
    },
    {
        "id": "packetsdk",
        "name": "PacketSDK",
        "description": "Run PacketSDK to earn rewards by sharing internet bandwidth.",
        "instructions": '1. Register an account at <a href="https://www.packetsdk.com/signUp.html" target="_blank">Packetsdk</a> to get your appkey.<br>2. Enter your appkey in the configuration field below.<br>3. Save the configuration and run the app to start earning rewards.',
        "docker_image": "packetsdk/packetsdk",
        "config_fields": ["appkey"],
        "config_type": "command",
        "command_template": "-appkey {appkey}",
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Paypal, Crypto",
        "supports_proxy": True,
    },
    {
        "id": "castarsdk",
        "name": "Castar SDK",
        "description": "Run Castar SDK to earn rewards by contributing to data collection.",
        "instructions": "1. Visit the <a href='https://www.castarsdk.com/register?c=c1b1d7b8'>Castar SDK website</a> and sign up to obtain your KEY.<br>2. Enter your KEY in the configuration field below.<br>3. Save the configuration and run the app to start earning rewards.",
        "docker_image": "ghcr.io/adfly8470/castarsdk/castarsdk@sha256:881cdbe79f10dbfac65a1de0673587f67059b650f8cd94cd71801cc52a435f53",
        "config_fields": ["key"],
        "config_type": "environment",
        "environment_map": {"KEY": "key"},
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Paypal, Crypto",
        "supports_proxy": True,
    },
    {
        "id": "wipter",
        "name": "Wipter",
        "description": "Run Wipter to earn passive income by sharing unused internet bandwidth.",
        "instructions": "1. Visit the <a href='wipter.com/register?via=5BBC6FF956'>Wipter</a> to signup.<br>2.Obtain your email and password.<br>3. Enter your Wipter email and password in the configuration fields below.<br>4. Save the configuration and run the app to start earning rewards.",
        "docker_image": "ghcr.io/adfly8470/wipter/wipter@sha256:339e6a23d6fd9a787fc35884b81d1dea9d169c40e902789ed73cb6b79621fba2",
        "config_fields": ["email", "password"],
        "config_type": "environment",
        "environment_map": {"WIPTER_EMAIL": "email", "WIPTER_PASSWORD": "password"},
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto",
        "supports_proxy": True
    },
    {
        "id": "uprock",
        "name": "Uprock",
        "description": "Run Uprock node to earn rewards by sharing your internet.",
        "instructions": "1. Register an account on <a href='https://link.uprock.com/i/1869fdc5'>Uprock</a>.</br>2. In the app configuration, set the port (default: 6000) and VNC password (default: sharetoearn).",
        "docker_image": "ghcr.io/adfly8470/uprock/uprock@sha256:c41be1805b47fde433883d11a11b04e2064846d5aafe162fc12aa0340bb0703b",
        "config_fields": ["port", "vnc_password"],
        "config_type": "environment",
        "environment_map": {
            "VNC_PASSWORD": "vnc_password",
            "VNC_PORT": "vnc_port",
            "WEBSOCKIFY_PORT": "port"

        },
        "port_mappings": {
            "5111": "port"
        },
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto",
        "supports_proxy": True,
        "claim_info": "Visit <a href='http://localhost:{port}/vnc.html' target='_blank'>http://localhost:{port}</a> to access your Uprock node."
    },
    {
        "id": "ebesucher",
            "name": "Ebesucher",
            "description": "Run Firefox in a Docker container to automatically visit websites and earn money with Ebesucher's surfbar.",
            "instructions": """
        1. Register an account at <a href="https://www.ebesucher.com/?ref=vanhbaka" target="_blank">Ebesucher</a> if you haven't already.<br>
        2. Enter your Ebesucher username in the configuration below.<br>
        3. Choose a port for accessing the Firefox web interface (e.g., 5800).<br>
        4. Start the container.<br>
        """,
            "docker_image": "jlesage/firefox",
            "config_fields": ["username", "web_port"],
            "config_type": "environment",
            "environment_map": {"FF_OPEN_URL": "https://www.ebesucher.com/surfbar/{username}"},
            "port_mappings": {"5800": "web_port"},
            "volume_mounts": ["./ebesucher-config:/config"],
            "max_devices_per_account": "Unlimited",
            "devices_per_ip": 1,
            "payment": "Paypal",
            "supports_proxy": True,
            "claim_info": "Visit <a href='http://localhost:{web_port}' target='_blank'>http://localhost:{web_port}</a> to access the Firefox interface and manage your Ebesucher surfbar. Note: If you experience disconnections, ensure you have selected a sufficient memory profile."
        },
    {
        "id": "adnade",
        "name": "Adnade",
        "description": "Run Firefox in a Docker container to automatically visit websites and earn money with Adnade's service.",
        "instructions": """
            1. Register an account at <a href="https://adnade.net/?ref=vanhbaka" target="_blank">Adnade</a> if you haven't already.<br>
            2. Enter your Adnade username in the configuration below.<br>
            3. Choose a port for accessing the Firefox web interface (e.g., 5800).<br>
            4. Start the container.<br>
            """,
        "docker_image": "jlesage/firefox",
        "config_fields": ["username", "web_port"],
        "config_type": "environment",
        "environment_map": {"FF_OPEN_URL": "https://adnade.net/view.php?user={username}&multi=4"},
        "port_mappings": {"5800": "web_port"},
        "volume_mounts": ["./adnade-config:/config"],
        "max_devices_per_account": "Unlimited",
        "devices_per_ip": 1,
        "payment": "Crypto, Paypal",
        "supports_proxy": True,
        "supports_datacenter_ip": True,
        "claim_info": "Visit <a href='http://localhost:{web_port}' target='_blank'>http://localhost:{web_port}</a> to access the Firefox interface and manage your Adnade service. Note: If you experience disconnections, ensure you have selected a sufficient memory profile."
    }
]