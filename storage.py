import boto3
from botocore.client import Config
from dotenv import load_dotenv
import os
from datetime import datetime
import mimetypes

load_dotenv()

class SpaceStorage:
    def __init__(self):
        self.space_name = os.getenv('DO_SPACE_NAME')
        self.region = os.getenv('DO_REGION')
        self.endpoint = f'https://{os.getenv("DO_ENDPOINT")}'
        self.access_token = os.getenv('DO_ACCESS_TOKEN')

        self.s3 = boto3.client(
            's3',
            region_name=self.region,
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_token,
            aws_secret_access_key=self.access_token,
            config=Config(signature_version='s3v4')
        )

    def upload_cv(self, user_id: str, file_content: bytes, original_filename: str) -> str:
        """
        Upload a CV file to DigitalOcean Spaces
        
        Args:
            user_id: Telegram user ID
            file_content: The CV file content in bytes
            original_filename: Original filename of the CV
            
        Returns:
            str: URL of the uploaded file
        """
        # Generate a unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        extension = os.path.splitext(original_filename)[1]
        filename = f'cvs/{user_id}/{timestamp}{extension}'
        
        # Detect content type
        content_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
        
        # Upload file
        try:
            self.s3.put_object(
                Bucket=self.space_name,
                Key=filename,
                Body=file_content,
                ContentType=content_type,
                ACL='private'  # Make sure files are private
            )
            
            # Generate URL
            url = f'https://{self.space_name}.{self.endpoint}/{filename}'
            return url
            
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            raise

    def get_cv_url(self, filename: str) -> str:
        """
        Generate a presigned URL for downloading a CV
        
        Args:
            filename: The filename in the space
            
        Returns:
            str: Presigned URL for downloading the file
        """
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.space_name,
                    'Key': filename
                },
                ExpiresIn=3600  # URL expires in 1 hour
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {str(e)}")
            raise
