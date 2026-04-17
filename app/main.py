from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def root():
	return {'status': 'ok', 'message': 'Auth system placeholder'}

@app.get('/ping')
async def ping():
	return 'ping'
