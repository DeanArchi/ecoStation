from django.db import models


class MQTTServer(models.Model):
    ID_Server = models.CharField(max_length=5, primary_key=True)
    Url = models.TextField()
    Status = models.CharField(max_length=10)


class Category(models.Model):
    ID_Category = models.CharField(max_length=5, primary_key=True)
    Designation = models.CharField(max_length=255)


class MeasuredUnit(models.Model):
    ID_Measured_Unit = models.CharField(max_length=5, primary_key=True)
    Title = models.CharField(max_length=100)
    Unit = models.CharField(max_length=100)


class Station(models.Model):
    ID_Station = models.CharField(max_length=5, primary_key=True)
    City = models.CharField(max_length=30)
    _Name = models.CharField(max_length=255)
    Status = models.CharField(max_length=10)
    ID_Server = models.ForeignKey(MQTTServer, on_delete=models.CASCADE)
    ID_SaveEcoBot = models.CharField(max_length=20)
    Coordinates = models.PointField()


class Favorite(models.Model):
    User_Name = models.CharField(max_length=5, primary_key=True)
    ID_Station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='favorites', primary_key=True)

    class Meta:
        unique_together = ('User_Name', 'ID_Station')


class OptimalValue(models.Model):
    ID_Category = models.ForeignKey(Category, on_delete=models.CASCADE, primary_key=True)
    ID_Measured_Unit = models.CharField(MeasuredUnit, on_delete=models.CASCADE, primary_key=True)
    Bottom_Border = models.DecimalField(max_digits=10, decimal_places=2)
    Upper_Border = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('ID_Category', 'ID_Measured_Unit')
        category = models.ForeignKey(Category, on_delete=models.CASCADE)
        measured_unit = models.ForeignKey(MeasuredUnit, on_delete=models.CASCADE)


class Measurment(models.Model):
    ID_Measurment = models.CharField(max_length=10, primary_key=True)
    _Time = models.DateTimeField()
    _Value = models.DecimalField(max_digits=10, decimal_places=2)
    ID_Station = models.ForeignKey(Station, on_delete=models.CASCADE)
    ID_Measured_Unit = models.ForeignKey(MeasuredUnit, on_delete=models.CASCADE)


class MQTTUnit(models.Model):
    ID_Station = models.ForeignKey(Station, on_delete=models.CASCADE, primary_key=True)
    ID_Measured_Unit = models.ForeignKey(MeasuredUnit, on_delete=models.CASCADE, primary_key=True)
    _Message = models.CharField(max_length=255)
    _Order = models.IntegerField()

    class Meta:
        unique_together = ('ID_Station', 'ID_Measured_Unit')
