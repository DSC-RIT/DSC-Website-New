from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate('./firebase_config.json')

firebase_admin.initialize_app(cred, {
    'storageBucket': 'dsc-website-debbf.appspot.com'
})


bucket = storage.bucket()
print(bucket)

def upload_image(source_file_name, destination_name):
    blob = bucket.blob('hello.txt')
    output = './hello.txt'
    with open(output, 'rb') as my_file:
        blob.upload_from_file(my_file)



def download_image(source_file_name, destination_name):
    blob = bucket.blob(source_file_name)
    blob.download_to_filename(destination_name)


    print('File {} uploaded to {}.'.format(
        source_file_name,
        destination_name))


def list_buckets():
    """Lists all buckets."""
    blobs = bucket.list_blobs()

    print(blobs.num_results)



app = Flask(__name__)


@app.route("/", methods=["POST"])
def login():
    image = request.get_data()
    upload_image('image.png', 'image.png')
    # download_image("https://firebasestorage.googleapis.com/v0/b/dsc-website-debbf.appspot.com/o/DeepinScreenshot_20190921193121.png?alt=media&token=097d249f-0ca6-44b8-916a-c49dbf067c49", "image.png")
    # list_buckets()
    return "Hello World"


if __name__=='__main__':
    app.run(debug=True)