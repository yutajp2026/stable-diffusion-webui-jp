import ngrok

# Connect to ngrok for ingress
def connect(token, port, options):
    account = None
    if token is None:
        token = 'None'
    else:
        if ':' in token:
            # token = authtoken:username:password
            token, username, password = token.split(':', 2)
            account = f"{username}:{password}"

    # For all options see: https://github.com/ngrok/ngrok-py/blob/main/examples/ngrok-connect-full.py
    if not options.get('authtoken_from_env'):
        options['authtoken'] = token
    if account:
        options['basic_auth'] = account
    if not options.get('session_metadata'):
        options['session_metadata'] = 'stable-diffusion-webui'


    try:
        public_url = ngrok.connect(f"127.0.0.1:{port}", **options).url()
    except Exception as e:
        print(f'無効な ngrok オートトークンですか？ngrok 接続は次の理由で中止されました: {e}\n'
              f'あなたのトークン: {token}, https://dashboard.ngrok.com/get-started/your-authtoken で正しいものを取得してください')
    else:
        print(f'ngrok は localhost:{port} に接続されました! URL: {public_url}\n'
               '起動が完了した後、このリンクを使用できます。')
