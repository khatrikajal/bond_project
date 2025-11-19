class VerificationSession:

    @staticmethod
    def set_mobile_verified(request, mobile):
        request.session["verified_mobile"] = mobile
        request.session["mobile_verified"] = True
        request.session.modified = True

    @staticmethod
    def set_email_verified(request, email):
        request.session["verified_email"] = email
        request.session["email_verified"] = True
        request.session.modified = True

    @staticmethod
    def is_mobile_verified(request):
        return request.session.get("mobile_verified", False)

    @staticmethod
    def is_email_verified(request):
        return request.session.get("email_verified", False)
