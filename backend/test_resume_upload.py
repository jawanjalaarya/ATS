#!/usr/bin/env python3
"""Test resume upload functionality."""

import requests
import tempfile
import os

BASE_URL = "http://localhost:8000/api/v1"

# Step 1: Login as recruiter
print("=" * 60)
print("Testing Resume Upload")
print("=" * 60)

login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "recruiter@example.com", "password": "recruiter123"},
    cookies={}
)

if login_response.status_code == 200:
    print("✓ Login successful")
    cookies = login_response.cookies
else:
    print(f"✗ Login failed: {login_response.status_code}")
    exit(1)

# Step 2: Create a test PDF
print("\nCreating test PDF file...")
pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(John Doe - Software Engineer) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000235 00000 n
0000000309 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
402
%%EOF"""

# Save to temp file
with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
    f.write(pdf_content)
    temp_pdf = f.name

try:
    # Step 3: Upload the resume
    print(f"Uploading test PDF: {temp_pdf}")
    
    with open(temp_pdf, 'rb') as f:
        files = {
            'file': ('test_resume.pdf', f, 'application/pdf')
        }
        upload_response = requests.post(
            f"{BASE_URL}/candidates/upload",
            files=files,
            data={},
            cookies=cookies
        )
    
    if upload_response.status_code in [200, 201]:
        data = upload_response.json()
        print(f"✓ Resume uploaded successfully!")
        print(f"  Candidate ID: {data['id']}")
        print(f"  Name: {data.get('name', 'N/A')}")
        print(f"  Email: {data.get('email', 'N/A')}")
        print(f"  Status: {data.get('status', 'N/A')}")
        print(f"  Resume path: {data.get('resume_path', 'N/A')}")
    else:
        print(f"✗ Upload failed: {upload_response.status_code}")
        print(f"Response: {upload_response.text}")
        
finally:
    # Clean up temp file
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)

print("\n" + "=" * 60)
print("✓ Resume upload test completed!")
print("=" * 60)
