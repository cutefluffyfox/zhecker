import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import environ


email_types = {
    'verification': '<h1>Welcome to our testing system Zhecker!</h1><p>You are at the last stage to start solving problems. To confirm your email, click on<b><a href="https://zhecker.herokuapp.com/email_verification?action_type=submit&email=%email%&verification_key=%verification_key%"><div style="color:rgb(160, 210, 160);">this link</div></a></b></p><p>If you do not confirm it within an hour, you will have to register again. If you have inadvertently received this email, click<b><a href="https://zhecker.herokuapp.com/email_verification?action_type=remove&email=%email%&verification_key=%verification_key%"><div style="color:rgb(210, 160, 160);">right here</div></a></b></p>',
    'verification_plain': 'Welcome to our testing system Zhecker!\n\nYou are at the last stage to start solving problems. To confirm your email, click on this link: https://zhecker.herokuapp.com/email_verification?action_type=submit&email=%email%&verification_key=%verification_key%\n\nIf you do not confirm it within an hour, you will have to register again. If you have inadvertently received this email, click right here: https://zhecker.herokuapp.com/email_verification?action_type=remove&email=%email%&verification_key=%verification_key%',
    'verification_subject': 'Email verification',
    'creator_confirmed': '<h1>Hello %name% %surname%!</h1><p>We are happy to tell you that your application to become a Creator has been <b>approved</b>.</p><p>Now you can:<ul><li>create contests</li><li>create tasks</li></ul></p><p>We are waiting for interesting contests and tasks from you, good luck!</p>',
    'creator_confirmed_plain': 'Hello %name% %surname%!\n\nWe are happy to tell you that your application to become a Creator has been approved.\n\nNow you can:\ncreate contests\ncreate tasks.\n\nWe are waiting for interesting contests and tasks from you, good luck!',
    'creator_confirmed_subject': 'Creator status confirmed',
    'creator_denied': '<h1>Hello %name% %surname%!</h1><p>We are sorry to tell you that your application to become a Creator has been <b>denied</b>.<p>We hope that some time later we will be able to give you that access. You can write us later. But for now, good luck in solving problems!</p>',
    'creator_denied_plain': 'Hello %name% %surname%!\n\nWe are sorry to tell you that your application to become a Creator has been denied.\n\nWe hope that some time later we will be able to give you that access. You can write us later. But for now, good luck in solving problems!',
    'creator_denied_subject': 'Creator status denied',
    'get_creator': '<h1>Hello!</h1><p>One more user want to become a creator. Here what they say:</p><p style="text-align: center;"><em>%message%</em></p><p style="text-align: left;">To confirm their new status click&nbsp;<span style="color: #008000;"><a style="color: #008000;" href="https://zhecker.herokuapp.com/creator_confirmation?action_type=submit&user_id=%user_id%&confirmation_key=%confirmation_key%">right here</a></span></p><p style="text-align: left;">If something wrong, please click&nbsp;<span style="color: #993300;"><a style="color: #993300;" href="https://zhecker.herokuapp.com/creator_confirmation?action_type=deny&user_id=%user_id%&confirmation_key=%confirmation_key%">here</a></span></p>',
    'get_creator_plain': 'Hello!\n\nOne more user want to become a creator. Here what they say:\n\n%message%\n\nTo confirm their new status click right here:\n\n https://zhecker.herokuapp.com/creator_confirmation?action_type=submit&user_id=%user_id%&confirmation_key=%confirmation_key%\n\nIf something wrong, please click here: \n\nhttps://zhecker.herokuapp.com/creator_confirmation?action_type=deny&user_id=%user_id%&confirmation_key=%confirmation_key%',
    'get_creator_subject': 'New creator'
}


def send_email(receiver: str, content_type: str, **kwargs) -> bool:
    try:
        message = MIMEMultipart('alternative')
        message['From'] = environ['MAIL_LOGIN_GOOGLE']
        message['To'] = receiver
        message['Subject'] = email_types[f"{content_type}_subject"]
        plain_text = email_types[f"{content_type}_plain"]
        html_text = email_types[content_type]
        for key in kwargs:
            plain_text = plain_text.replace(f"%{key}%", str(kwargs[key]))
            html_text = html_text.replace(f"%{key}%", str(kwargs[key]))
        message.attach(MIMEText(plain_text, 'plain'))
        message.attach(MIMEText(html_text, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(environ['MAIL_LOGIN_GOOGLE'], environ['MAIL_PASSWORD_GOOGLE'])
            smtp.sendmail(environ['MAIL_LOGIN_GOOGLE'], receiver, message.as_string())
        return True
    except smtplib.SMTPException:
        return False
