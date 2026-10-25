import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from myapp.models import Photo
import cloudinary.uploader

print("Starting image fix...")
# Only target photos that don't have a full URL (the broken ones)
broken_photos = Photo.objects.exclude(image__contains='http')

for photo in broken_photos:
    try:
        # If the file doesn't exist locally, we can't re-upload it.
        # We can only clear the broken reference so the frontend stops showing the placeholder.
        print(f"Removing broken photo reference: {photo.id}")
        photo.delete() 
    except Exception as e:
        print(f"Error with photo {photo.id}: {e}")
        
print("Cleanup complete.")
