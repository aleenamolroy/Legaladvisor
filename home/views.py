import datetime
import os
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
import smtplib
from .utils import sendsms  
import pymysql
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import EmailMultiAlternatives
import uuid
from django.urls import reverse
from django.db import  transaction
from django.core.exceptions import ValidationError
import re
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

now = datetime.datetime.now()
conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
c = conn.cursor()

def index(request):
    return render(request,'index.html')


from django.contrib.auth.hashers import make_password, check_password

#------------------------user registration------------------------------------------
from django.contrib.auth.hashers import make_password

#------------------------user registration------------------------------------------
def register(request):
    data = {}  

    if request.method == 'POST':
        user_type = request.POST.get('userType')
        myfile = request.FILES["img"]
        id_proof_file = request.FILES["idProofFile"]

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        
        id_proof_fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
        id_proof_filename = id_proof_fs.save(id_proof_file.name, id_proof_file)
        id_proof_uploaded_file_url = id_proof_fs.url(id_proof_filename)

        common_data = {
            "name": request.POST.get("name"),
            "age": request.POST.get("age"),
            "gender": request.POST.get("gender"),
            "email": request.POST.get("email"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "password": make_password(request.POST.get("password")),  # Hash the password
            "state": request.POST.get("state"),
            "district": request.POST.get("district"),
            "id_proof_type": request.POST.get("idProofType"),
            "id_proof_url": id_proof_uploaded_file_url,
            "pincode": request.POST.get("pincode"),
        }

        if user_type == 'advocate':
            advocate_data = {
                "enrollment_number": request.POST.get("enrollmentNumber"),
                "qualification1": request.POST.get("qualifications1"),
                "qualification2": request.POST.get("qualifications2"),
            }
            return register_advocate(request, common_data, advocate_data, uploaded_file_url, data)
        else:
            return register_client(request, common_data, uploaded_file_url, data)

    return render(request, "register.html", {"data": data})

def register_advocate(request, common_data, advocate_data, uploaded_file_url, data):
    # Check in tbl_user for existing email or phone
    s1 = "SELECT COUNT(*) FROM tbl_user WHERE email = %s OR phone = %s"
    c.execute(s1, (common_data['email'], common_data['phone']))
    reg_count = c.fetchone()

    if reg_count[0] == 0:
        # Insert into tbl_user
        s2 = """INSERT INTO tbl_user (u_img, u_name, gender, age, email, phone, address, 
        state, district, pincode, id_proof_type, id_proof_url, password, u_type, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'advocate', 0)"""

        c.execute(s2, (uploaded_file_url, common_data['name'], common_data['gender'], common_data['age'], 
                       common_data['email'], common_data['phone'], common_data['address'], common_data['state'], 
                       common_data['district'], common_data['pincode'], common_data['id_proof_type'], common_data['id_proof_url'], 
                       common_data['password']))
        conn.commit()

        user_id = c.lastrowid
        
        # Insert into tbl_advocate
        s3 = """INSERT INTO tbl_advocate (Entrollmentno, adv_qualification1, adv_qualification2, u_id, status) 
        VALUES (%s, %s, %s, %s,  0)"""
        qualifications = ', '.join([advocate_data['qualification1'], advocate_data['qualification2']])
        
        c.execute(s3, (advocate_data['enrollment_number'], advocate_data['qualification1'], advocate_data['qualification2'], user_id))
        conn.commit()

        msg = "Advocate Registered Successfully, Your Account will be activated soon."
        data["msg"] = msg
        return render(request, "register.html", {"data": data})
    else:
        msg = "Account Already Exists"
        data["msg"] = msg
        return render(request, "register.html", {"data": data})

def register_client(request, common_data, uploaded_file_url, data):
    s1 = "SELECT COUNT(*) FROM tbl_user WHERE email = %s OR phone = %s"
    c.execute(s1, (common_data['email'], common_data['phone']))
    reg_count = c.fetchone()

    if reg_count[0] == 0:
        s2 = """INSERT INTO tbl_user (u_img, u_name,gender,age,email,phone,address, 
                state, district, pincode,id_proof_type, id_proof_url,password,u_type, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,  %s, %s,'client', 1)"""
        c.execute(s2, (uploaded_file_url, common_data['name'], common_data['gender'], common_data['age'], 
                       common_data['email'], common_data['phone'], common_data['address'], common_data['state'], 
                       common_data['district'], common_data['pincode'], common_data['id_proof_type'], common_data['id_proof_url'], 
                       common_data['password']))
        conn.commit()

        user_id = c.lastrowid
        s3 = "INSERT INTO tbl_client (u_id, status) VALUES (%s, 1)"
        c.execute(s3, (user_id,))
        conn.commit()

        msg = "Client Registered Successfully, Your Account will be activated soon."
        data["msg"] = msg
        return render(request, "register.html", {"data": data})
    else:
        msg = "Account Already Exists"
        data["msg"] = msg
        return render(request, "register.html", {"data": data})

#---------------------------------------- login-------------------------------------------------------------
#---------------------------------------- login-------------------------------------------------------------
def login(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")

        s1 = "SELECT * FROM tbl_user WHERE email = %s"
        c.execute(s1, (email,))
        user_details = c.fetchone()

        if not user_details:
            msg = "User Does Not Exist"
            return render(request, "login.html", {"msg": msg})

        hashed_password = user_details[15]  # Password is at index 15
        u_id = user_details[0]  # ID is at index 0
        u_type = user_details[16]  # User type is at index 16
        status = user_details[17]  # Status is at index 17

        if not check_password(password, hashed_password):
            msg = "Incorrect Password"
            return render(request, "login.html", {"msg": msg})

        if status != 1:
            msg = "Your account is not activated"
            return render(request, "login.html", {"msg": msg})

        if u_type == 'admin':
            request.session["admin_id"] = u_id
            return HttpResponseRedirect("/admin_home")
        elif u_type == 'advocate':
            # Check if advocate has selected a category
            s2 = "SELECT category FROM tbl_advocate WHERE u_id = %s"
            c.execute(s2, (u_id,))
            cat_id = c.fetchone()[0]
            
            request.session["adv_id"] = u_id
            
            if not cat_id:
                return HttpResponseRedirect("/adv_home/select_category")
            
            return HttpResponseRedirect("/adv_home")
        elif u_type == 'client':
            request.session["client_id"] = u_id
            return HttpResponseRedirect("/client_home")

        msg = "Invalid user type or credentials"
        return render(request, "login.html", {"msg": msg})

    return render(request, "login.html")
#------------------------------select category----------------------------------
def select_category(request):
    if not request.session.get("adv_id"):
        return HttpResponseRedirect("/login")
    
    adv_id = request.session.get("adv_id")
    
    if request.method == 'POST':
        category_id = request.POST.get("category_id")
        
        # Update the selected category in the database
        s3 = "UPDATE tbl_advocate SET category = %s WHERE u_id = %s"
        c.execute(s3, (category_id, adv_id))
        conn.commit()
        
        return HttpResponseRedirect("/adv_home")
    
    # Fetch available categories from the database
    with conn.cursor() as cursor:
        cursor.execute("SELECT cat_id, category_name FROM tbl_category")
        categories = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    
    # Render the select_category.html template with the list of categories
    return render(request, "advocate/select_category.html", {"categories": categories})
#---------------------------Logout----------------------------------------------#
def logout(request):
    request.session.flush()
    return redirect("login")
#--------------------------forgot password--------------------------------------
#--------------------------password-reset---------------------------------------
def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tbl_user WHERE email = %s", [email])
            user = cursor.fetchone()
            
            if user:
                token = str(uuid.uuid4())
                reset_url = f'http://127.0.0.1:8000/reset/{token}/'
                subject = 'Password Reset'
                message = f'Click the following link to reset your password: {reset_url}'
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [email]
                
                email_message = EmailMultiAlternatives(subject, message, from_email, to_email)
                email_message.send()
                
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO password_reset (user_email, token) VALUES (%s, %s)", [email, token])
                    conn.commit()
                msg="Password reset link has been sent to your mail. Kindly check your mail and follow the procedures"
                return render(request, "login.html", {"msg": msg})

            else:
                msg="User with this email does not exist"
                return render(request, "login.html", {"msg": msg})
    return render(request, 'login.html')
#--------------------------------password-confirmation-------------------------------------------------------------------
def password_reset_confirm(request, token):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_email FROM password_reset WHERE token = %s", [token])
                result = cursor.fetchone()
                
                if result:
                    email = result[0]
                    cursor.execute("SELECT u_id FROM tbl_user WHERE email = %s", [email])
                    user_id = cursor.fetchone()
                    
                    if user_id:
                        user_id = user_id[0]
                        hashed_password = make_password(new_password)  # Hashing the new password
                        cursor.execute("UPDATE tbl_user SET password = %s WHERE u_id = %s", [hashed_password, user_id])
                        conn.commit()

                        cursor.execute("DELETE FROM password_reset WHERE token = %s", [token])
                        conn.commit()

                        return redirect('login')
                return render(request, 'password_reset_confirm.html', {'error': 'Invalid or expired token', 'token': token})
        else:
            return render(request, 'password_reset_confirm.html', {'error': 'Passwords do not match', 'token': token})

    return render(request, 'password_reset_confirm.html', {'token': token})
#---------------------------------password-confirmation-end---------------------------------------------

#----------------------------------------Admin-----------------------------------#
def admin_home(request):
    
    if "admin_id" not in request.session:
        return redirect("login")
    response = render(request, 'admin/admin_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response
#--------------------------------------Advocate-request-----------------------------
def adv_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    return render(request,'admin/adv_req.html')

def adv_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        s1 = """
        SELECT a.Entrollmentno, u.u_name, u.u_img, u.age, u.email, u.phone, a.adv_qualification1,
               a.adv_qualification2, u.state, u.district, u.pincode, u.id_proof_type, u.id_proof_url, u.u_id
        FROM tbl_advocate a
        JOIN tbl_user u ON a.u_id = u.u_id
        WHERE u.status = '0' AND u.u_type = 'advocate'
        """
        print("SQL Query:", s1)

        c.execute(s1)
        data = c.fetchall()

        print("Fetched Data:", data)

        if not data:
            msg = "No Requests to show...."
            return render(request, "admin/adv_req.html", {"msgg": msg})
        
        # Convert the fetched data into a list of dictionaries
        data_list = []
        for row in data:
            data_list.append({
                "Entrollmentno": row[0],
                "u_name": row[1],
                "u_img": row[2].replace('/media/', ''),
                "age": row[3],
                "email": row[4],
                "phone": row[5],
                "adv_qualification1": row[6],
                "adv_qualification2": row[7],
                "state": row[8],
                "district": row[9],
                "pincode": row[10],
                "id_proof_type": row[11],
                "id_proof_url": row[12],
                "u_id": row[13]
            })

        print("Data List:", data_list)  # Debug print for data list
        
        return render(request, "admin/adv_req.html", {"data": data_list, "MEDIA_URL": settings.MEDIA_URL})

    except Exception as e:
        print("Exception occurred:", e)  # Print the exception
        return render(request, "admin/adv_req.html", {"msgg": f"An error occurred: {str(e)}"})

def action_adv(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        reg_id = request.GET.get("reg_id")
        status = request.GET.get("st")
        if status == "Approve":
            update_query = "UPDATE tbl_user SET status='1' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_adv = "UPDATE tbl_advocate SET status='1' WHERE u_id=%s"
            c.execute(update_query_adv, (reg_id,))
            conn.commit()

            # Fetch the user's phone number
            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            # Send SMS
            message = "Your advocate request has been approved."
            sendsms(phone_number, message)

            return redirect("/admin_home/adv_req/")

        elif status == "Reject":
            update_query = "UPDATE tbl_user SET status='2' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_adv = "UPDATE tbl_advocate SET status='2' WHERE u_id=%s"
            c.execute(update_query_adv, (reg_id,))
            conn.commit()
            # Fetch the user's phone number
            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            # Send SMS
            message = "Your advocate request has been rejected."
            sendsms(phone_number, message)

            return redirect("/admin_home/adv_req/")

    except Exception as e:
        return render(request, "admin/adv_req.html", {"msgg": f"An error occurred: {str(e)}"})
#---------------------client request----------------------------------------------------------->
def client_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    return render(request,'admin/client_req.html')
def client_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        s1 = """
        SELECT a.c_id, u.u_name,u.u_img, u.age, u.email, u.phone,  u.state, u.district, u.pincode, u.u_id
        FROM tbl_client a
        JOIN tbl_user u ON a.u_id = u.u_id
        WHERE u.status = '0' AND u.u_type = 'client'
        """
        print("SQL Query:", s1)

        c.execute(s1)
        data = c.fetchall()

        print("Fetched Data:", data)

        if not data:
            msg = "No Requests to show...."
            return render(request, "admin/client_req.html", {"msgg": msg})
        
        data_list = []
        for row in data:
            data_list.append({
                "c_id": row[0],
                "u_name": row[1],
                "u_img": row[2],
                "age": row[3],
                "email": row[4],
                "phone": row[5],
                "state": row[6],
                "district": row[7],
                "pincode": row[8],
                "u_id": row[9]
            })
        
        return render(request, "admin/client_req.html", {"data": data_list})

    except Exception as e:
        return render(request, "admin/client_req.html", {"msgg": f"An error occurred: {str(e)}"})


def action_client(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        reg_id = request.GET.get("reg_id")
        status = request.GET.get("st")
        if status == "Approve":
            update_query = "UPDATE tbl_user SET status='1' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_client = "UPDATE tbl_client SET status='1' WHERE u_id=%s"
            c.execute(update_query_client, (reg_id,))
            conn.commit()

            verify_query = "SELECT status FROM tbl_client WHERE u_id=%s"
            c.execute(verify_query, (reg_id,))
            client_status = c.fetchone()[0]
            print("Updated client status (Approve):", client_status)

            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            message = "Your client request has been approved."
            sendsms(phone_number, message)

            return redirect("/admin_home/client_req/")

        elif status == "Reject":
            update_query = "UPDATE tbl_user SET status='2' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_client = "UPDATE tbl_client SET status='2' WHERE u_id=%s"
            c.execute(update_query_client, (reg_id,))
            conn.commit()

            verify_query = "SELECT status FROM tbl_client WHERE u_id=%s"
            c.execute(verify_query, (reg_id,))
            client_status = c.fetchone()[0]
            print("Updated client status (Reject):", client_status)

            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            message = "Your client request has been rejected."
            sendsms(phone_number, message)

            return redirect("/admin_home/client_req/")

    except Exception as e:
        print("Exception occurred:", e)  
        return render(request, "admin/client_req.html", {"msgg": f"An error occurred: {str(e)}"})
#--------------------------------------- User list ----------------------------------------------------------
#----------------------------------------advocate list-------------------------------------------------------
def approved_advocates_list(request):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_id, u.u_name, u.email, u.phone, u.state, u.district, a.Entrollmentno, u.u_img, u.age, 
                   a.adv_qualification1, a.adv_qualification2, u.pincode, 
                   u.id_proof_type, u.id_proof_url
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_type = 'advocate' AND u.status = 1 AND a.status = 1
        """)
        rows = cursor.fetchall()

    # Prepare data to include a flag for PDF detection
    advocates = []
    for row in rows:
        is_pdf = row[13].lower().endswith('.pdf')  # Assuming 'id_proof_url' is at index 13
        advocate_data = {
            'u_id': row[0],  # Include u_id
            'u_name': row[1],
            'email': row[2],
            'phone': row[3],
            'state': row[4],
            'district': row[5],
            'Entrollmentno': row[6],
            'u_img': row[7],
            'age': row[8],
            'adv_qualification1': row[9],
            'adv_qualification2': row[10],
            'pincode': row[11],
            'id_proof_type': row[12],
            'id_proof_url': row[13],
            'is_pdf': is_pdf
        }
        advocates.append(advocate_data)

    return render(request, 'admin/approved_advocate_list.html', {'advocates': advocates})
#----------------------------------------client list --------------------------------------------------------

def client_list(request):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_id, u.u_name, u.email, u.phone, u.state, u.district, u.u_img, u.age, 
                   u.pincode, u.id_proof_type, u.id_proof_url
            FROM tbl_user u
            WHERE u.u_type = 'client' AND u.status = 1
        """)
        rows = cursor.fetchall()

    # Prepare data to include a flag for PDF detection
    clients = []
    for row in rows:
        is_pdf = row[10].lower().endswith('.pdf')  # Assuming 'id_proof_url' is at index 10
        client_data = {
            'u_id': row[0],  # Include u_id
            'u_name': row[1],
            'email': row[2],
            'phone': row[3],
            'state': row[4],
            'district': row[5],
            'u_img': row[6],
            'age': row[7],
            'pincode': row[8],
            'id_proof_type': row[9],
            'id_proof_url': row[10],
            'is_pdf': is_pdf
        }
        clients.append(client_data)

    return render(request, 'admin/client_list.html', {'clients': clients})

#----------------------------------delete advocate------------------------------------------------------------
def delete_advocate(request, u_id):
    with conn.cursor() as cursor:
        # Update the status of the advocate to 2 (disabled)
        cursor.execute("UPDATE tbl_user SET status = 2 WHERE u_id = %s AND u_type = 'advocate'", [u_id])
        cursor.execute("UPDATE tbl_advocate SET status = 2 WHERE u_id = %s", [u_id])
        conn.commit()
    
    # Redirect back to the approved advocates list
    return HttpResponseRedirect('/admin_home/approved_advocates/')
#----------------------------------delete client---------------------------------------------------------------
def delete_client(request, u_id):
    with conn.cursor() as cursor:
        # Update the status of the client to 2 (disabled)
        cursor.execute("UPDATE tbl_user SET status = 2 WHERE u_id = %s AND u_type = 'client'", [u_id])
        cursor.execute("UPDATE tbl_client SET status = 2 WHERE u_id = %s", [u_id])
        conn.commit()
    
    # Redirect back to the client list
    return HttpResponseRedirect('/admin_home/client_list/')
#---------------------------------advocate---------------------------------------------------------
def adv_home(request):
    if "adv_id" not in request.session:
        return redirect("login")
    response = render(request, 'advocate/adv_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response

#-------------------------------advocate profile view -------------------------------------------------------
def advocate_profile(request):
    if not request.session.get("adv_id"):
        return HttpResponseRedirect("/login")

    adv_id = request.session.get("adv_id")
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.u_img, u.u_name, u.gender, u.age, u.email, u.phone, 
                u.address, u.state, u.district, u.pincode, 
                u.id_proof_type, u.id_proof_url, 
                a.Entrollmentno, a.adv_qualification1, a.adv_qualification2
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_id = %s
        """, [adv_id])
        
        advocate_details = cursor.fetchone()
    
    if advocate_details:
        data = {
            "img_url": advocate_details[0],
            "name": advocate_details[1],
            "gender": advocate_details[2],
            "age": advocate_details[3],
            "email": advocate_details[4],
            "phone": advocate_details[5],
            "address": advocate_details[6],
            "state": advocate_details[7],
            "district": advocate_details[8],
            "pincode": advocate_details[9],
            "id_proof_type": advocate_details[10],
            "id_proof_url": advocate_details[11],
            "enrollment_number": advocate_details[12],
            "qualification1": advocate_details[13],
            "qualification2": advocate_details[14],
        }
    else:
        data = {"msg": "Profile not found"}

    return render(request, "advocate/advocate_profile.html", {"data": data})
#---------------------------------------advocate prfile update-----------------------------------------------
def advocate_profile_update(request):
    data = {}

    # Ensure the user is logged in
    if 'adv_id' not in request.session:
        return HttpResponseRedirect('/login')

    user_id = request.session['adv_id']

    if request.method == 'POST':
        # Get the profile data from the form
        name = request.POST.get("name")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        state = request.POST.get("state")
        district = request.POST.get("district")
        pincode = request.POST.get("pincode")
        taluk = request.POST.get("taluk")
        village = request.POST.get("village")
        id_proof_type = request.POST.get("idProofType")
        id_proof_file = request.FILES.get("idProofFile")
        img = request.FILES.get("img")
        enrollment_number = request.POST.get("enrollmentNumber")
        qualification1 = request.POST.get("qualifications1")
        qualification2 = request.POST.get("qualifications2")

        with conn.cursor() as cursor:
            # Check if email or phone is being updated to an existing user's email or phone
            cursor.execute("""
                SELECT COUNT(*) 
                FROM tbl_user 
                WHERE (email = %s OR phone = %s) 
                AND u_id != %s
            """, [email, phone, user_id])
            count = cursor.fetchone()[0]

            if count == 0:
                # Update profile image if a new one is uploaded
                if img:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    img_filename = fs.save(img.name, img)
                    img_url = fs.url(img_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET u_img = %s 
                        WHERE u_id = %s
                    """, [img_url, user_id])

                # Update ID proof if a new one is uploaded
                if id_proof_file:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    id_proof_filename = fs.save(id_proof_file.name, id_proof_file)
                    id_proof_url = fs.url(id_proof_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET id_proof_url = %s 
                        WHERE u_id = %s
                    """, [id_proof_url, user_id])

                # Update the rest of the profile information in tbl_user
                cursor.execute("""
                    UPDATE tbl_user 
                    SET u_name = %s, age = %s, gender = %s, email = %s, phone = %s, address = %s, state = %s, district = %s, pincode = %s, taluk = %s, village = %s, id_proof_type = %s
                    WHERE u_id = %s
                """, [name, age, gender, email, phone, address, state, district, pincode, taluk, village, id_proof_type, user_id])

                # Update advocate-specific information in tbl_advocate
                cursor.execute("""
                    UPDATE tbl_advocate 
                    SET Entrollmentno = %s, adv_qualification1 = %s, adv_qualification2 = %s
                    WHERE u_id = %s
                """, [enrollment_number, qualification1, qualification2, user_id])

                # Commit the transaction
                conn.commit()

                # Update session data if needed
                request.session['adv_name'] = name
                request.session['adv_email'] = email
                request.session['adv_phone'] = phone

                data["msg"] = "Profile updated successfully."
            else:
                data["msg"] = "Email or phone already exists."

    # Fetch current profile data
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_img, u.u_name, u.age, u.gender, u.email, u.phone, u.address, u.state, u.district, u.pincode, u.taluk, u.village, u.id_proof_type, u.id_proof_url,
                   a.Entrollmentno, a.adv_qualification1, a.adv_qualification2
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_id = %s
        """, [user_id])
        user_details = cursor.fetchone()

    if not user_details:
        data["msg"] = "Profile not found."
    else:
        profile_data = {
            "u_img": user_details[0],
            "name": user_details[1],
            "age": user_details[2],
            "gender": user_details[3],
            "email": user_details[4],
            "phone": user_details[5],
            "address": user_details[6],
            "state": user_details[7],
            "district": user_details[8],
            "pincode": user_details[9],
            "taluk": user_details[10],
            "village": user_details[11],
            "id_proof_type": user_details[12],
            "id_proof_url": user_details[13],
            "enrollment_number": user_details[14],
            "qualification1": user_details[15],
            "qualification2": user_details[16],
        }
        data["profile"] = profile_data

    return render(request, "advocate/advocate_profile_update.html", {"data": data})

#--------------------------------change password-------------------------------------------------------
def change_password_adv(request):
    if 'adv_id' not in request.session:
        print("Client ID not found in session, redirecting to login")
        return HttpResponseRedirect("/login")
    
    client_id = request.session['adv_id']
    print("Advocate ID found in session:", client_id)

    if request.method == 'POST':
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        print("Received POST data:", current_password, new_password, confirm_password)

        if new_password != confirm_password:
            msg = "New passwords do not match"
            print(msg)
            return render(request, "advocate/change_password_adv.html", {"msg": msg})

        with conn.cursor() as c:
            # Assuming client_id is the same as user_id in tbl_login
            s1 = "SELECT password FROM tbl_user WHERE u_id = %s"
            c.execute(s1, (client_id,))
            user_details = c.fetchone()

            if not user_details:
                msg = "User does not exist"
                print(msg)
                return render(request, "advocate/change_password_adv.html", {"msg": msg})

            hashed_password = user_details[0]  

            if not check_password(current_password, hashed_password):
                msg = "Incorrect current password"
                print(msg)
                return render(request, "advocate/change_password_adv.html", {"msg": msg})

            new_hashed_password = make_password(new_password)
            
            s2 = "UPDATE tbl_user SET password = %s WHERE u_id = %s"
            c.execute(s2, (new_hashed_password, client_id))
            conn.commit()  # Commit the transaction

        msg = "Password changed successfully"
        print(msg)
        return render(request, "advocate/change_password_adv.html", {"msg": msg})

    return render(request, "advocate/change_password_adv.html")
#--------------------------------------add case history ------------------------------------------------------
def validate_case_number(case_number):
    if not re.match(r'^CASE-\d{4}-\d{4}$', case_number):
        raise ValidationError('Case number must be in the format CASE-YYYY-NNNN.')
def add_case(request):
    if not request.session.get("adv_id"):
        return redirect('login')

    adv_id = request.session.get("adv_id")  # Get advocate ID from session
    category_choices = []

    # Fetch categories for the dropdown
    with conn.cursor() as cursor:
        cursor.execute("SELECT cat_id, category_name FROM tbl_category")
        categories = cursor.fetchall()
        category_choices = [(cat_id[0], cat_id[1]) for cat_id in categories]

    if request.method == 'POST':
        case_number = request.POST.get('case_number')
        case_name = request.POST.get('case_name')
        case_status = request.POST.get('case_status')
        case_date = request.POST.get('case_date')
        days_taken = request.POST.get('days_taken')
        court_name = request.POST.get('court_name')
        case_category = request.POST.get('case_category')

        # Validate the case number format
        try:
            validate_case_number(case_number)
        except ValidationError as e:
            return render(request, 'advocate/add_case.html', {
                'error_message': str(e),
                'category_choices': category_choices
            })

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tbl_case_history (advocate_id, case_number, case_name, case_status, case_date, days_taken, court_name, case_category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [adv_id, case_number, case_name, case_status, case_date, days_taken, court_name, case_category])
                conn.commit()
        except Exception as e:
            print("Error inserting data:", e)
            conn.rollback()

        return redirect('add_case')  # Redirect to a success page or another page

    return render(request, 'advocate/add_case.html', {'category_choices': category_choices})

#---------------------------------------client----------------------------------------------------------------
def client_home(request):
    if "client_id" not in request.session:
        return redirect("login")
    
    response = render(request, 'client/client_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response
##---------------------------------client profile view---------------------------------------------------------

def client_profile_view(request):
    if 'client_id' not in request.session:
        return HttpResponseRedirect('/login')

    client_id = request.session['client_id']

    # Fetch client details
    s1 = "SELECT * FROM tbl_user WHERE u_id = %s"
    c.execute(s1, (client_id,))
    user_details = c.fetchone()

    if not user_details:
        msg = "Client profile not found."
        return render(request, "client/client_profile_view.html", {"msg": msg})

    profile_data = {
        "name": user_details[2],
        "age": user_details[4],
        "gender": user_details[3],
        "email": user_details[5],
        "phone": user_details[6],
        "address": user_details[7],
        "state": user_details[8],
        "district": user_details[9],
        "pincode": user_details[10],
        "taluk": user_details[11],
        "village": user_details[12],
        "id_proof_type": user_details[13],
        "id_proof_url": user_details[14],
        "u_img": user_details[1],  # Assuming user image is at index 0
    }

    # Determine if ID proof is a PDF
    idproof_is_pdf = profile_data['id_proof_url'].endswith('.pdf') if profile_data['id_proof_url'] else False

    return render(request, "client/client_profile_view.html", {
        "profile_data": profile_data,
        "idproof_is_pdf": idproof_is_pdf
    })
#------------------------------client profile update-------------------------------------------------------------

def client_profile_update(request):
    data = {}
    
    # Ensure the user is logged in
    if 'client_id' not in request.session:
        return HttpResponseRedirect('/login')
    
    user_id = request.session['client_id']

    if request.method == 'POST':
        # Get the profile data from the form
        name = request.POST.get("name")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        state = request.POST.get("state")
        district = request.POST.get("district")
        pincode = request.POST.get("pincode")
        taluk = request.POST.get("taluk")
        village = request.POST.get("village")
        id_proof_type = request.POST.get("idProofType")
        id_proof_file = request.FILES.get("idProofFile")
        img = request.FILES.get("img")

        with conn.cursor() as cursor:
            # Check if email or phone is being updated to an existing user's email or phone
            cursor.execute("""
                SELECT COUNT(*) 
                FROM tbl_user 
                WHERE (email = %s OR phone = %s) 
                AND u_id != %s
            """, [email, phone, user_id])
            count = cursor.fetchone()[0]

            if count == 0:
                # Update profile image if a new one is uploaded
                if img:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    img_filename = fs.save(img.name, img)
                    img_url = fs.url(img_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET u_img = %s 
                        WHERE u_id = %s
                    """, [img_url, user_id])

                # Update ID proof if a new one is uploaded
                if id_proof_file:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    id_proof_filename = fs.save(id_proof_file.name, id_proof_file)
                    id_proof_url = fs.url(id_proof_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET id_proof_url = %s 
                        WHERE u_id = %s
                    """, [id_proof_url, user_id])

                # Update the rest of the profile information
                cursor.execute("""
                    UPDATE tbl_user 
                    SET u_name = %s, age = %s, gender = %s, email = %s, phone = %s, address = %s, state = %s, district = %s, pincode = %s, taluk = %s, village = %s, id_proof_type = %s
                    WHERE u_id = %s
                """, [name, age, gender, email, phone, address, state, district, pincode, taluk, village, id_proof_type, user_id])

                conn.commit()  

                # Update session data if needed
                request.session['client_name'] = name
                request.session['client_email'] = email
                request.session['client_phone'] = phone

                data["msg"] = "Profile updated successfully."
            else:
                data["msg"] = "Email or phone already exists."

    # Fetch current profile data
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u_img, u_name, age, gender, email, phone, address, state, district, pincode, taluk, village, id_proof_type, id_proof_url 
            FROM tbl_user 
            WHERE u_id = %s
        """, [user_id])
        user_details = cursor.fetchone()

    if not user_details:
        data["msg"] = "Profile not found."
    else:
        profile_data = {
            "u_img": user_details[0],
            "name": user_details[1],
            "age": user_details[2],
            "gender": user_details[3],
            "email": user_details[4],
            "phone": user_details[5],
            "address": user_details[6],
            "state": user_details[7],
            "district": user_details[8],
            "pincode": user_details[9],
            "taluk": user_details[10],
            "village": user_details[11],
            "id_proof_type": user_details[12],
            "id_proof_url": user_details[13],
        }
        data["profile"] = profile_data

    return render(request, "client/client_profile_update.html", {"data": data})
#----------------------------change password------------------------------------------------
def change_password(request):
    if 'client_id' not in request.session:
        print("Client ID not found in session, redirecting to login")
        return HttpResponseRedirect("/login")
    
    client_id = request.session['client_id']
    print("Client ID found in session:", client_id)

    if request.method == 'POST':
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        print("Received POST data:", current_password, new_password, confirm_password)

        if new_password != confirm_password:
            msg = "New passwords do not match"
            print(msg)
            return render(request, "change_password.html", {"msg": msg})

        with conn.cursor() as c:
            # Assuming client_id is the same as user_id in tbl_login
            s1 = "SELECT password FROM tbl_user WHERE u_id = %s"
            c.execute(s1, (client_id,))
            user_details = c.fetchone()

            if not user_details:
                msg = "User does not exist"
                print(msg)
                return render(request, "change_password.html", {"msg": msg})

            hashed_password = user_details[0]  

            if not check_password(current_password, hashed_password):
                msg = "Incorrect current password"
                print(msg)
                return render(request, "change_password.html", {"msg": msg})

            new_hashed_password = make_password(new_password)
            
            s2 = "UPDATE tbl_user SET password = %s WHERE u_id = %s"
            c.execute(s2, (new_hashed_password, client_id))
            conn.commit()  # Commit the transaction

        msg = "Password changed successfully"
        print(msg)
        return render(request, "change_password.html", {"msg": msg})

    return render(request, "change_password.html")
#--------------------------------find-advocate-------------------------------------------------------
'''def get_advocates(request):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            u.u_id, u.u_img, u.u_name, u.district, u.email, u.phone, 
            a.adv_qualification1, a.adv_qualification2, a.adv_qualification3, 
            a.Entrollmentno
        FROM tbl_user u 
        JOIN tbl_advocate a ON u.u_id = a.u_id 
        WHERE u.u_type = 'advocate'
    """)
    advocates = cursor.fetchall()

    # Process advocates to partially hide email and phone
    advocate_list = []
    for advocate in advocates:
        advocate_dict = {
            'id': advocate[0],
            'profile_picture': advocate[1],
            'name': advocate[2],
            'district': advocate[3],
            'email': advocate[4][:3] + "*****" + advocate[4][-3:],  # Partially hide email
            'phone': advocate[5][:2] + "*****" + advocate[5][-2:],  # Partially hide phone
            'qualification': ', '.join([advocate[6], advocate[7], advocate[8]]),  # Concatenate qualifications
            'enrollment_no': advocate[9]
        }
        advocate_list.append(advocate_dict)

    return render(request, 'client/advocate_display.html', {'advocates': advocate_list})'''
#-------------------------------------advocate - search --------------------------------------------------
def get_advocate_list():
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.u_id, u.u_name, u.gender, u.age, u.address, u.state, u.district, 
                u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_type, 
                u.email, u.phone, u.u_img, c.category_name,
                AVG(r.rating) AS average_rating, COUNT(r.rating_id) AS review_count
            FROM 
                tbl_user u
            LEFT JOIN 
                tbl_advocate a ON u.u_id = a.u_id
            LEFT JOIN 
                tbl_category c ON a.category = c.cat_id
            LEFT JOIN 
                tbl_rating r ON a.u_id = r.advocate_id
            WHERE 
                u.u_type = 'advocate' AND u.status = 1
            GROUP BY 
                u.u_id, u.u_name, u.gender, u.age, u.address, u.state, u.district, 
                u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_type, 
                u.email, u.phone, u.u_img, c.category_name
        """)
        columns = [col[0] for col in cursor.description]
        results = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    return results

def advocate_list(request):
    client_id = request.session.get('client_id')
    advocates = get_advocate_list()

    for advocate in advocates:
        # Masking the phone numbers and email addresses
        advocate['phone'] = advocate['phone'][:3] + '****' + advocate['phone'][-2:]
        advocate['email'] = advocate['email'].split('@')[0][:3] + '****' + '@' + advocate['email'].split('@')[1]

        # Fetch the request status for each advocate
        cursor = conn.cursor()
        cursor.execute('''
            SELECT status FROM tbl_client_request 
            WHERE advocate_id = %s AND client_id = %s
        ''', (advocate['u_id'], client_id))
        result = cursor.fetchone()
        advocate['request_status'] = result[0] if result else -1

    return render(request, 'client/advocate_list.html', {
        'advocates': advocates,
        'star_range': list(range(1, 6))
    })
@csrf_exempt
def send_request(request):
    if 'client_id' not in request.session:
        print("Client ID not found in session, redirecting to login")
        return HttpResponseRedirect("/login")
    
    client_id = request.session['client_id']
    print("Client ID found in session:", client_id)

    if request.method == 'POST':
        advocate_id = request.POST.get('advocate_id')
        request_date = timezone.now()
        status = 0  # Default status for a new request

        try:
           
            cursor = conn.cursor()

            # Insert the request into the database
            cursor.execute('''INSERT INTO tbl_client_request (advocate_id, client_id, request_date, status)
                              VALUES (%s, %s, %s, %s)''', (advocate_id, client_id, request_date, status))
            conn.commit()

            return JsonResponse({'message': 'Request sent successfully!'})

        except conn.Error as e:
            return JsonResponse({'error': str(e)}, status=500)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({'error': 'Invalid request'}, status=400)

def check_request_status(request):
    if 'client_id' not in request.session:
        return JsonResponse({'error': 'Client ID not found'}, status=400)

    client_id = request.session['client_id']
    
    if request.method == 'POST':
        advocate_id = request.POST.get('advocate_id')

     
        cursor = conn.cursor()

        try:
            # Query the database to check the request status
            cursor.execute('''SELECT status FROM tbl_client_request 
                              WHERE advocate_id = %s AND client_id = %s''',
                           (advocate_id, client_id))
            result = cursor.fetchone()

            if result:
                status = result[0]
            else:
                status = -1  # Indicates no request found

            return JsonResponse({'status': status})

        except conn.Error as e:
            return JsonResponse({'error': str(e)}, status=500)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({'error': 'Invalid request'}, status=400)
#------------------------------------ request accept or reject advocate ----------------------------------------

def client_requests(request):
    adv_id = request.session.get('adv_id')  # Ensure advocate is logged in
    if not adv_id:
        return HttpResponseRedirect('/login')

    cursor = conn.cursor()
    cursor.execute('''
    SELECT cr.req_id, u.u_name, u.phone, u.email, u.district, u.u_img, cr.status
    FROM tbl_client_request cr
    JOIN tbl_client c ON cr.client_id = c.u_id
    JOIN tbl_user u ON c.u_id = u.u_id
    WHERE cr.advocate_id = %s
    ''', [adv_id])
    requests = cursor.fetchall()


    # Format requests into dictionaries
    client_requests = [
        {
           'id': r[0],
           'name': r[1],
           'phone': r[2],
           'email': r[3],
           'district': r[4],
           'image': r[5],
            'status': r[6]
        } for r in requests
    ]

    return render(request, 'advocate/client_request.html', {'requests': client_requests})

@csrf_exempt
def update_request_status(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        new_status = request.POST.get('status')

        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE tbl_client_request
                SET status = %s
                WHERE req_id = %s
            ''', [new_status, request_id])
            conn.commit()
            return JsonResponse({'message': 'Request updated successfully!'})
        except conn.Error as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            cursor.close()
            conn.close()

    return JsonResponse({'error': 'Invalid request'}, status=400)
