from django.db import models
class RatingAgency(models.TextChoices):
    CRISIL = "CRISIL", "CRISIL"
    ICRA = "ICRA", "ICRA"
    CARE = "CARE", "CARE Ratings"
    IND_RA = "IND-RA", "India Ratings & Research"
    BWR = "BWR", "Brickwork Ratings"
    ACUITE = "ACUITE", "Acuité Ratings"

class CreditRating(models.TextChoices):
    AAA = "AAA", "AAA"
    AA_PLUS = "AA+", "AA+"
    AA = "AA", "AA"
    AA_MINUS = "AA-", "AA-"
    A_PLUS = "A+", "A+"
    A = "A", "A"
    A_MINUS = "A-", "A-"
    BBB_PLUS = "BBB+", "BBB+"
    D = "UNRATED", "UNRATED"