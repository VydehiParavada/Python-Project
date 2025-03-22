
import calendar
from django.db import models
from decimal import Decimal
from django.db.models import F, Sum, Count, Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timezone, timedelta
from django.db.models.functions import ExtractYear, ExtractMonth, Cast, Coalesce
import datetime
import plotly.express as px
from plotly.offline import plot
from django.contrib.auth.models import User


import pandas as pd


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=255, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True, default="")
    


    class Meta:
        managed = False
        db_table = 'categories'
    
    def __str__(self):
        return (
    		self.category_name
        )
    
    @property
    def category(self):
        return self.category_name


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=255, blank=False, null=False) #required
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    is_active= models.BooleanField(default=True)
    
    
    class Meta:
        managed = True
        db_table = 'customers'
     
    def CustomerOrders(self):
        orders = Order.objects.all().filter(customer = self.customer_id)
        return orders
    
    def get_latest_order_date(self):
        latest_order = Order.objects.filter(customer=self).aggregate(latest_order=Max('order_date'))
        print(latest_order['latest_order'])
        return latest_order['latest_order']
 
    def is_inactive(self):
        one_year_ago = datetime.datetime.now().date() - timedelta(days=365)
        latest_order_date = self.get_latest_order_date()
 
        if latest_order_date:
            if latest_order_date > one_year_ago:
                self.is_active = True
                self.save()
                return True
            else:
                self.is_active = False
                self.save()
                return False
        else:
            return True   
    
    def NumberOfOrders(self):
        orders = Order.objects.all().filter(customer = self.customer_id)
        return orders.count()  
    
           
    def get_activity_status(self): 
        return "Active" if self.is_active else "Inactive"

    def __str__(self):
        return (
    		self.customer_name 
      		+ " [Contact: "+ self.contact_name +  "]"
        )
    # v3.2 Added - Member function in Customers class to generate Orders Plot based on supplied year
    def OrdersPlacedPlot(self, year):
   

        customerOrders = self.CustomerOrders().order_by('order_date').annotate(
          Year = ExtractYear("order_date"),
          Month = ExtractMonth("order_date"),
          CustomerName = F('customer__customer_name'),
          OrderTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity')),
          NumberOfProducts = Count('orderdetail'),

        )
        
        if year: 
            customerOrders = customerOrders.filter(Year__contains= year)

        if customerOrders.count()==0:
            return '<div> No Orders placed</div>'
         
        ordersdFrame = pd.DataFrame(
          list(customerOrders.values())
        )
        
        fig = px.bar(
            ordersdFrame,
            x='order_date',
            y= 'OrderTotal',
            color='order_id',
            labels={'color':'order_id'},
            text_auto=True,
        )
        
        figure_title = 'Orders by Date for '  + self.customer_name
      
        fig.update_layout(
            title = figure_title,
            xaxis_title="",
            yaxis_title="Year Order Placed",
        )
        
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_tickprefix = '$', 
            yaxis_tickformat = ',.2f'
            )
        plot_html = plot(fig, output_type='div')
        
        return plot_html

    # v3.2 Generate a list of objects for the total sales revenue from orders placed each year by the current customer - "self".
    def AnnualOrders(self):
        
        annualOrders = self.CustomerOrders().annotate(
          Year = Cast(F("order_date__year"),output_field=models.CharField()),
          OrderTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'), 
                           distinct=True),
        ).values('Year', 'OrderTotal').order_by("Year")
        

        annuals =pd.DataFrame(list(annualOrders)) 
        print(annuals)
        annuals = annuals.groupby("Year").agg("sum").reset_index()
        print(annuals)
        
        fig = px.bar(annuals,x='Year', y='OrderTotal', 
                     color='Year', text_auto=True,
                    )

        fig.update_layout(
            title = 'Annual Orders',
            xaxis_title="Order Year",
            yaxis_title="Order Total",
        )
        
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_tickprefix = '$', 
            yaxis_tickformat = ',.2f'
        )

        plot_html = plot(fig, output_type='div')
        
        return plot_html

    # v3.2 Generate a plot of products and their total sales revenue from orders placed by the current customer - "self".
    def ProductReveues(self):
        
        
        productOrders = self.CustomerOrders().order_by('order_date').annotate(
            ProductName = F('orderdetail__product__product_name'),
            CategoryName = F('orderdetail__product__category__category_name'),
            TotalQuantity = Sum('orderdetail__quantity'),
            ProductTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'),distinct=True),
           
        ).distinct()

        
        productOrders = productOrders.values('ProductName', 'ProductTotal', 'CategoryName').order_by('CategoryName')


        productsData =pd.DataFrame(list(productOrders)) 
        productsData = productsData.groupby('ProductName').agg("sum").reset_index()
        print(productsData)
        
        fig = px.bar(productsData,x='ProductName', y='ProductTotal', 
                     color='ProductName', text_auto=True,                    )
               
        fig.update_layout(
            title = 'Revenues from Products',
            xaxis_title="Products",
            yaxis_title="Revenue",
        )
        
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_tickprefix = '$', 
            yaxis_tickformat = ',.2f'
        )


        plot_html = plot(fig, output_type='div')
        
        return plot_html

    # v3.2 Generate a plot of products and their total sales revenue from orders placed by the current customer - "self".
    def ProductsSoldPlot(self):
        
        
        # Year is extracted from order_date using the "__" for year ()
        # This is another method to get components of a datetime object, in addition to the "ExtractYear" function
        productOrders = self.CustomerOrders().order_by('order_date').annotate(
            ProductName = F('orderdetail__product__product_name'),
            CategoryName = F('orderdetail__product__category__category_name'),
            TotalQuantity = Sum('orderdetail__quantity'),
            ProductTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'),distinct=True),
            #Year = Cast(F("order_date__year"), output_field=models.CharField()),
        ).distinct()

        
        productOrders = productOrders.values('ProductName', 'ProductTotal', 'TotalQuantity')


        productsData =pd.DataFrame(list(productOrders)) 
        productsData = productsData.groupby('ProductName').agg("sum").reset_index()
        print(productsData)
        
        fig = px.bar(productsData,x='ProductName', y='TotalQuantity', 
                     color='ProductName', text_auto=True)
                # Format Chart and Axes titles 
        fig.update_layout(
            title = 'Products Quantities',
            xaxis_title="Products",
            yaxis_title="Revenue",
        )
        
        # Colors and formats - remove legend.
        fig.update_layout(
            coloraxis_showscale=False,
        )


        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html

    # v3.2 Generate a plot of products and their total sales revenue from orders placed by the current customer - "self".
    def ProductCategoryRevenusPlot(self):
        
        # Year is extracted from order_date using the "__" for year ()
        # This is another method to get components of a datetime object, in addition to the "ExtractYear" function
        categoryOrders = self.CustomerOrders().order_by('order_date').annotate(
            #ProductName = F('orderdetail__product__product_name'),
            CategoryName = F('orderdetail__product__category__category_name'),
            CategoryTotalQuantity = Sum('orderdetail__quantity'),
            CategoryTotalRevenue = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'),distinct=True),
            #Year = Cast(F("order_date__year"), output_field=models.CharField()),
        ).distinct()

        categoryOrders = categoryOrders.values('CategoryName', 'CategoryTotalRevenue')
       
        print(list(categoryOrders))

        categoryData =pd.DataFrame(list(categoryOrders)) 
        categoryData = categoryData.groupby("CategoryName").agg("sum").reset_index()

        print(categoryData)
        
        fig = px.bar(categoryData,x='CategoryName', y='CategoryTotalRevenue', 
                     color='CategoryName', text_auto=True,)
                # Format Chart and Axes titles 
        fig.update_layout(
            title = 'Category Sales Revenues',
            xaxis_title="Category",
            yaxis_title="Sales Revenue from Category",
        )
        
        # Colors and formats - remove legend.
        fig.update_layout(
            coloraxis_showscale=False,
        )


        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html
    
    # v3.2 Generate a plot of products and their total sales revenue from orders placed by the current customer - "self".
    def ProductCategorySalesPlot(self):
        
        # Year is extracted from order_date using the "__" for year ()
        # This is another method to get components of a datetime object, in addition to the "ExtractYear" function
        categoryOrders = self.CustomerOrders().order_by('order_date').annotate(
            #ProductName = F('orderdetail__product__product_name'),
            CategoryName = F('orderdetail__product__category__category_name'),
            CategoryTotalQuantity = Sum('orderdetail__quantity'),
            #ProductTotal = Sum(F('orderdetail__product__price')*F('orderdetail__quantity'),distinct=True),
            #Year = Cast(F("order_date__year"), output_field=models.CharField()),
        ).distinct()

        
        categoryOrders = categoryOrders.values('CategoryName', 'CategoryTotalQuantity').order_by("CategoryTotalQuantity")
       
        print(list(categoryOrders))

        categoryData =pd.DataFrame(list(categoryOrders)) 
        categoryData = categoryData.groupby("CategoryName").agg("sum").reset_index()

        print(categoryData)
        
        fig = px.bar(categoryData,x='CategoryName', y='CategoryTotalQuantity', 
                     color='CategoryName', text_auto=True,)
                # Format Chart and Axes titles 
        fig.update_layout(
            title = 'Category Sales',
            xaxis_title="Category",
            yaxis_title="# of Products Bought with Category",
        )
        
        # Colors and formats - remove legend.
        fig.update_layout(
            coloraxis_showscale=False,
        )


        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html



class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    
    # category_id = models.IntegerField(blank=True, null=True)
    # I am not using on_delete=models.Cascade because I dont want to delete categories when a product is deleted.
    # Also note the name change, since category_id is in the DB, this should just be category.
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    
    unit = models.CharField(max_length=255, blank=True, null=True)
    
    # Must define a price.
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    is_available = models.BooleanField(default=True)
 
    
    # Method to return the customers who purchased this product
    def PurchasedBy(self):
        CustomersWhoBoughtProduct = Customer.objects.filter(
            order__orderdetail__product_id=self.product_id
        ).distinct()
        return CustomersWhoBoughtProduct
    
    def customer_purchase_summary(self):
        purchase_summary = OrderDetail.objects.filter(product=self).values('order__customer__customer_name').annotate(
            total_quantity=Sum('quantity'),
            total_orders=Count('order')
        )
        return purchase_summary
    
    def get_product_latest_order_date(self):
        product_latest_order = OrderDetail.objects.filter(product=self).aggregate(latest_order_date=Max('order__order_date'))
        print(product_latest_order['latest_order_date'])
        return product_latest_order['latest_order_date']
 
    def get_availabilityStatus(self):
        one_year_ago = datetime.datetime.now().date() - timedelta(days=365)
        product_latest_order_date = self.get_product_latest_order_date()
 
        if product_latest_order_date:
            if product_latest_order_date > one_year_ago:
                self.is_available = True
                self.save()
                return "Yes"
            else:
                self.is_available = False
                self.save()
                return "No"
        else:
            return "Yes"
    ################## assng 3 2.A starts############
    def AnnualProductOrders(self, year=None):
        orders = OrderDetail.objects.filter(product=self)
        if year:
            orders = orders.filter(order__order_date__year=year)
 
        orders = orders.annotate(
            Year=ExtractYear(F("order__order_date")),
            OrderTotal=Sum(F('product__price') * F('quantity'))
        ).values('Year', 'OrderTotal').order_by('Year')
 
        data_frame = pd.DataFrame(list(orders))
        if data_frame.empty:
            return '<div>No annual data available.</div>'
 
        fig = px.bar(
            data_frame,
            x='Year',
            y='OrderTotal',
            text_auto=True,
            color='Year',
            labels={'OrderTotal': 'Total Revenue', 'Year': 'Year'}
        )
        fig.update_layout(
            title='Annual Sales',
            xaxis_title='Year',
            yaxis_title='Revenue',
            yaxis_tickprefix='$',
            coloraxis_showscale=False,
        )
        return plot(fig, output_type='div')
 
    def MonthlyProductOrders(self, year=None):
        orders = OrderDetail.objects.filter(product=self)
        if year:
            orders = orders.filter(order__order_date__year=year)
 
        orders = orders.annotate(
            Month=ExtractMonth(F("order__order_date")),
            OrderTotal=Sum(F('product__price') * F('quantity'))
        ).values('Month', 'OrderTotal').order_by('Month')
 
        data_frame = pd.DataFrame(list(orders))
        if not data_frame.empty:
            data_frame['Month'] = data_frame['Month'].apply(lambda x: calendar.month_name[x])
       
        if data_frame.empty:
            return '<div>No monthly data available.</div>'
 
        fig = px.bar(
            data_frame,
            x='Month',
            y='OrderTotal',
            text_auto=True,
            color='Month',
            labels={'OrderTotal': 'Total Revenue', 'Month': 'Month'}
        )
        fig.update_layout(
            title='Monthly Sales',
            xaxis_title='Month',
            yaxis_title='Revenue',
            yaxis_tickprefix='$',
            coloraxis_showscale=False,
        )
        return plot(fig, output_type='div')
    
################## assng 3 2.C starts############

    def total_sales(self, year=None):
     
        orders = Order.objects.all()
 
        if year:
            orders = orders.filter(order__order_date__year=year)
 
        total_quantity = orders.aggregate(
            total_quantity=Coalesce(Sum('quantity'), 0)
        )['total_quantity']
 
        total_revenue = orders.aggregate(
            total_revenue=Coalesce(Sum(F('quantity') * F('product__price')), 0)
        )['total_revenue']
 
        return total_quantity, total_revenue
    
       
 ################## assng 3 2.D starts############
 
    def ProductCategorySalesAnalysisPlot(self):
        category_orders = (
            OrderDetail.objects  # Filter by the specific product
            .values('product__category__category_name')  # Group by category name
            .annotate(CategoryTotalQuantity=Sum('quantity'))  # Sum the quantity sold
            .order_by('product__category__category_name')  # Ensure ordered by category name
        )
 
        category_data = pd.DataFrame(list(category_orders))
        if category_data.empty:
            return "<div>No data available for Product Category Sales</div>"
       
        print(category_data)
 
        fig = px.bar(
            category_data,
            x='product__category__category_name', 
            y='CategoryTotalQuantity', 
            color='product__category__category_name',  
            text_auto=True,
            title='Category Sales for Product',
            labels={
                'product__category__category_name': 'Category',
                'CategoryTotalQuantity': '# of Products Sold',
            },
        )
 
        fig.update_layout(
            xaxis_title="Category",
            yaxis_title="# of Products Sold in Category",
            coloraxis_showscale=False,
            title_x=0.5,  
        )
       
        return plot(fig, output_type='div')
    
    def ProductCategoryRevenuesAnalysisPlot(self):
        category_orders = (
            OrderDetail.objects
            .values('product__category__category_name')  
            .annotate(
                CategoryTotalRevenue=Sum(F('product__price') * F('quantity')),  
            )
            .order_by('product__category__category_name')  
        )
 
        category_data = pd.DataFrame(list(category_orders))
        if category_data.empty:
            return "<div>No data available for Product Category Revenues</div>"
       
        print(category_data)
 

        fig = px.bar(
            category_data,
            x='product__category__category_name',  
            y='CategoryTotalRevenue',  
            color='product__category__category_name', 
            text_auto=True,
            title='Category Sales Revenues for Product',
            labels={
                'product__category__category_name': 'Category',
                'CategoryTotalRevenue': 'Sales Revenue',
            },
        )
 
        fig.update_layout(
            xaxis_title="Category",
            yaxis_title="Sales Revenue from Category",
            coloraxis_showscale=False,
            title_x=0.5,
        )
       
        return plot(fig, output_type='div')
    class Meta:
        managed = True
        db_table = 'products'






class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    #customer_id = models.IntegerField(blank=True, null=True)
    # I am not using on_delete=models.Cascade because I dont want to delete customers when an order is deleted.
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    # The order date will be added for the current date when the order is saved.
    order_date = models.DateField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'orders'
    
    def AllOrderDetails(self):
        orderdetails = OrderDetail.objects.filter(order = self.order_id)
        return orderdetails
    #v3.2
    def OrderTotal(self):
        orderDetails = OrderDetail.objects.filter(order = self.order_id)
        total = Decimal("0.0")
        
        for line in orderDetails:
            total += line.Total #(quantity*product.price)
        return total
    
    def AllOrderYears():
        '''
            Returns a queryset of each distinct year an order was placed,
            in chronological order
        '''
        allYears = Order.objects.all().annotate(
            Year = ExtractYear("order_date")
        ).order_by('Year').distinct()
       
        return allYears.values('Year')
    
    
    
class OrderDetail(models.Model):
    order_detail_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_details'
    
    @property
    def Total(self):
        return self.quantity*self.product.price
    
    @property
    def product_name(self):
        if (self.product):
            return self.product.product_name
        else:
            return ''
@receiver(post_save, sender=Order)
def update_customer_activity(sender, instance, **kwargs):     
    instance.customer.update_activity_status()

