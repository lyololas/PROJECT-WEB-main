import os
import requests
from PIL import Image
from io import BytesIO

def download_image(url, filename):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img.save(os.path.join('static', 'uploads', filename))
            print(f"Downloaded {filename}")
        else:
            print(f"Failed to download {filename}")
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")

def main():
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')

    images = {
        'diamond_hoodie.jpg': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=800&auto=format&fit=crop&q=60',
        'steve_tshirt.jpg': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&auto=format&fit=crop&q=60',
        'enderman_hoodie.jpg': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=800&auto=format&fit=crop&q=60',
        'logo_tshirt.jpg': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&auto=format&fit=crop&q=60',
        'nether_hoodie.jpg': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=800&auto=format&fit=crop&q=60'
    }

    for filename, url in images.items():
        if not os.path.exists(os.path.join('static', 'uploads', filename)):
            download_image(url, filename)

if __name__ == '__main__':
    main() 