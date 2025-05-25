download_data:
	wget https://raw.githubusercontent.com/wangpinggl/TREQS/refs/heads/master/mimicsql_data/mimicsql_natural_v2/test.json dataset/test.json

serve:
	nodemon -e py -x python main.py

etl:
	nodemon -e py -x python etl.py