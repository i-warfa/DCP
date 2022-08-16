# Downloading directories from AWS S3 bucket using cloudpathlib library:
``` python
    # Install cloudpathlib via pip and import the library:

    from cloudpathlib import CloudPath

    # Connect to the URI path of the desired object within the S3 bucket:

    cp = CloudPath("s3://bucket_name/folder_in_bucket")

    # Download the object to the desired local path on PC:

    cp.download_to("C:\\Users\\User\\Desktop\\folder_in_desktop")   
```

# Downloading directories from S3 bucket using the AWS CLI tool:
    Install AWS CLI with pip
    
    Run via terminal:   
    
    aws s3 sync s3://<bucket_name/folder_in_bucket> <local_path>

# Uploading local directories to AWS S3 bucket using the AWS CLI tool:
    Install AWS CLI with pip

    Run via terminal:   
    
    aws s3 <local_path> sync s3://<bucket_name/folder_in_bucket>
    
