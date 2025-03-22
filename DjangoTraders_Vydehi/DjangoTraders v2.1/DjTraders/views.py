from django.shortcuts import get_object_or_404, render, redirect
# v2.1 
#Add Create and Update Views to list of imported generic forms.
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import IntegrityError
from django.db.models import Sum, Count, F
from django.db.models import DecimalField, ExpressionWrapper
from django.db.models.functions import ExtractYear, ExtractMonth
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from datetime import timedelta

import io
import base64
import plotly.io as pio
from io import BytesIO
from datetime import date
# Create your views here.
from .models import Customer, Order, Product, Category, OrderDetail

# v2.1 
# Add imports from forms to be able to create forms using forms classes.
from .forms import CustomerForm
from .forms import ProductForm

# v3.0 Added Plotly Imports 
# use either graphs or express based on the kind of plot and lkevel of customization needed.

import plotly.graph_objects as graphs
import plotly.express as px
import pandas as pd

# plot allows generating plots in html components including divs.
from plotly.offline import plot

from django.core.serializers import serialize
from django.http import JsonResponse
from django.db.models import Count


def DjTradersHome(request):
    return render(request,'DjTraders/index.html',{})


################## assng 3 2.A starts############

class AnnualMonthlyProductView(DetailView):
    def get(self, request, pk):
        product = Product.objects.get(pk=pk)
        AnnualySalePlot=product.AnnualProductOrders()
        MonthlySalePlot=product.MonthlyProductOrders()
        
        
        return render(request, 'DjTraders/AnnualMonthlyProducts.html', {"product":product,'AnnualySalePlot':AnnualySalePlot,'MonthlySalePlot':MonthlySalePlot})
    

      
class DjTradersProductsView(ListView):
    model = Product
    template_name = 'DjTraders/products.html'
    context_object_name = 'products'
    #paginate_by=15  
    
    def all_categories(self):
        Categories = Category.objects.all().order_by('category_name').distinct()
        return Categories.values('category_name')
    
    def get_queryset(self):
        query = self.request.GET.get('ProductName', '')
        pricequery = self.request.GET.get('Price', '')
        categoryquery = self.request.GET.get('srchCategory', '')
        if query:
            products = self.model.objects.filter(product_name__icontains = query)
        elif categoryquery:
            products = self.model.objects.filter(category__category_name__icontains = categoryquery)
        elif pricequery:
            try:
                price = float(pricequery)
                price_operator = self.request.GET.get('PriceOperator', '')
                if price_operator == 'gte':
                    products = self.model.objects.filter(price__gte=price)
                elif price_operator == 'lte':
                    products = self.model.objects.filter(price__lte=price)
                else:
                    products = self.model.objects.filter(price=price)
            except ValueError:
                pass
        else:
            products = self.model.objects.all() 
       
        return products.order_by("product_name")
    
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        srchProductName = self.request.GET.get('ProductName', '')
        context["ProductName"] = srchProductName
        srchPrice = self.request.GET.get('Price', '')
        context["Price"] = srchPrice 
        searchCategory = self.request.GET.get('srchCategory', '')
        context['srchCategory'] = searchCategory
        context["Categories"] = self.all_categories
         
        return context
    
    ################## assng 3 2.A starts############
def ProductAnnualMonthlySales(request, pk=None):
    selOrderYear = request.GET.get('selOrderYear', "")
    product = get_object_or_404(Product, pk=pk)
 
    OrderYears = Order.AllOrderYears()
   
    annual_plot = product.AnnualProductOrders()
    monthly_plot = product.MonthlyProductOrders(year=selOrderYear if selOrderYear else None)
 
    return render(
        request,
        'DjTraders/AnnualMonthlyProducts.html',
        {
            'product': product,
            'selOrderYear': selOrderYear,
            'OrderYears': OrderYears,
            'AnnualySalePlot': annual_plot,
            'MonthlySalePlot': monthly_plot,
        }
    )
###########assng 3###    
def GetProductDetails(request):
    str_id = request.GET.get('product_id')
    id=int(str_id)          
    product = Product.objects.get(product_id=id)
    return render(request, 'DjTraders/ProductHome.html', 
                  {'product': product}) 
      
    ################## assng 3 2.b starts############
def plot_top_bottom_revenue_products(request, selOrderYear=None):
    
    OrderYears = Order.AllOrderYears()     
    selOrderYear = request.GET.get('selOrderYear', selOrderYear)    
    order_details_with_revenue = OrderDetail.objects.annotate(
        revenue=F('product__price') * F('quantity'),  
        year=ExtractYear('order__order_date')         
    )   
    if selOrderYear:
        order_details_with_revenue = order_details_with_revenue.filter(year=selOrderYear)
   
    revenue_per_product_year = order_details_with_revenue.values(
        'product__product_id', 'product__product_name', 'year'
    ).annotate(
        total_revenue=Sum('revenue')
    ).order_by('-total_revenue')  
    
    top_10 = list(revenue_per_product_year[:10])  
    bottom_10 = list(revenue_per_product_year[::-1][:10])  
     
    def generate_bar_chart(data, title, color_scale):
        df = pd.DataFrame({
            'Product': [item['product__product_name'] for item in data],
            'Total Revenue': [item['total_revenue'] for item in data]
        })
        fig = px.bar(
            df, x='Product', y='Total Revenue', title=title,
            labels={'Total Revenue': 'Revenue ($)', 'Product': 'Product Name'},
            color='Total Revenue', color_continuous_scale=color_scale
        )
        return plot(fig, output_type='div')
    
    top_10_html = generate_bar_chart(top_10, f'Top 10 Revenue-Generating Products in {selOrderYear or "All Years"}', 'Blues')
    bottom_10_html = generate_bar_chart(bottom_10, f'Bottom 10 Revenue-Generating Products in {selOrderYear or "All Years"}', 'Reds')
     
    context = {
        'top_10_plot': top_10_html,
        'bottom_10_plot': bottom_10_html,
        'selOrderYear': selOrderYear,
        'OrderYears': OrderYears,
    }
    return render(request, 'DjTraders/TopBottom.html', context)

################## assng 3 2.c starts############


def product_sales_analysis(request, pk):
    product = Product.objects.get(pk=pk)
   
    OrderYears = Order.AllOrderYears()  
    selOrderYear = request.GET.get('selOrderYear')
 
    total_sales_data = []
    if selOrderYear:
        orders = Order.objects.filter(orderdetail__product=product, order_date__year=selOrderYear)
    else:
        orders = Order.objects.filter(orderdetail__product=product)
 
    annual_data = orders.annotate(
        year=ExtractYear('order_date')
        ).values('year').annotate(
        total_orders=Count('order_id'),
        total_products_sold=Sum('orderdetail__quantity'),
        total_revenue=Sum(
            ExpressionWrapper(
                F('orderdetail__quantity') * F('orderdetail__product__price'),
                output_field=DecimalField()
            )
        )
    ).order_by('year')
 
    for year_data in annual_data:
        year = year_data['year']
        total_orders = year_data['total_orders']
        total_products_sold = year_data['total_products_sold']
        total_revenue = year_data['total_revenue']
 
        monthly_sales_data = []
       
    # Monthly sales data
        monthly_data = orders.filter(order_date__year=year).annotate(
        month=ExtractMonth('order_date')
        ).values('month').annotate(
        total_orders_month=Count('order_id'),
        total_products_sold_month=Sum('orderdetail__quantity'),
        total_revenue_month=Sum(
            ExpressionWrapper(
                F('orderdetail__quantity') * F('orderdetail__product__price'),
                output_field=DecimalField()
            )
        )
        ).order_by('month')
 
        avg_sales_data = {
            'avg_orders': total_orders / 12,
            'avg_products_sold': total_products_sold / 12,
            'avg_revenue': total_revenue / 12,
        }
 
        for month_data in monthly_data:
            month = month_data['month']
            total_orders_month = month_data['total_orders_month']
            total_products_sold_month = month_data['total_products_sold_month']
            total_revenue_month = month_data['total_revenue_month']
 
            comparison = {
                'orders_vs_avg': total_orders_month - avg_sales_data['avg_orders'],
                'products_sold_vs_avg': total_products_sold_month - avg_sales_data['avg_products_sold'],
                'revenue_vs_avg': total_revenue_month - avg_sales_data['avg_revenue'],
            }
 
            monthly_sales_data.append({
                'month': month,
                'total_orders_month': total_orders_month,
                'total_products_sold_month': total_products_sold_month,
                'total_revenue_month': total_revenue_month,
                'comparison': comparison,
            })
 
        total_sales_data.append({
            'year': year,
            'total_orders': total_orders,
            'total_products_sold': total_products_sold,
            'total_revenue': total_revenue,
            'monthly_sales': monthly_sales_data,
            'avg_sales': avg_sales_data
        })
 
    df_annual = pd.DataFrame(total_sales_data)
    df_annual['year'] = df_annual['year'].astype(int)
    df_annual['total_orders'] = pd.to_numeric(df_annual['total_orders'], errors='coerce')
    df_annual['total_revenue'] = pd.to_numeric(df_annual['total_revenue'], errors='coerce')
    df_annual['total_products_sold'] = pd.to_numeric(df_annual['total_products_sold'], errors='coerce')
   
    fig_annual = px.bar(df_annual, x='year', y=['total_orders', 'total_revenue', 'total_products_sold'],
                    title=f"Annual Sales for {product.product_name}")
    annual_chart_html = fig_annual.to_html(full_html=False)
 
 
    df_monthly = pd.DataFrame([{
        'Month': month_data['month'],
        'Orders': month_data['total_orders_month'],
        'Revenue': month_data['total_revenue_month'],
        'Comparison with Avg': month_data['comparison']['revenue_vs_avg']
    } for year_data in total_sales_data for month_data in year_data['monthly_sales']])
   
    df_monthly['Month'] = df_monthly['Month'].astype(int)
    df_monthly['Orders'] = pd.to_numeric(df_monthly['Orders'], errors='coerce')
    df_monthly['Revenue'] = pd.to_numeric(df_monthly['Revenue'], errors='coerce')
    df_monthly['Comparison with Avg'] = pd.to_numeric(df_monthly['Comparison with Avg'], errors='coerce')
 
    fig_monthly = px.line(df_monthly, x='Month', y='Revenue', title=f"Monthly Sales Comparison for {product.product_name}")
    monthly_chart_html = fig_monthly.to_html(full_html=False)
 
 
    context = {
        'product': product,
        'ProductAnnualySalesPlot': annual_chart_html,
        'ProductMonthlySalesPlot': monthly_chart_html,
        'OrderYears': Order.objects.all().values('order_date').distinct(),
        'selOrderYear': selOrderYear,
        'OrderYears': OrderYears,
    }
 
    return render(request, 'DjTraders/ProductSalesAnalysis.html', context)

################## assng 3 2.D starts############
def CategoryAnalysis(request, pk):
    product = get_object_or_404(Product, pk=pk)
 
    category_sales_plot = product.ProductCategorySalesAnalysisPlot()
    category_revenue_plot = product.ProductCategoryRevenuesAnalysisPlot()
 
    return render(
        request,
        'DjTraders/CategorySalesAnalysis.html',
        {
            'product': product,
            'CategoryRevenuesPlot': category_revenue_plot,
            'CategoryPlot': category_sales_plot,
        }
    )

 #assng 3  ends#################
def edit_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('DjTraders.Products')
        else:
            print(form.errors) 
    else:
        form = ProductForm()
    return render(request, 'product_form2.html', {'form': form})

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                return redirect('DjTraders.Products')
            except IntegrityError:
                form.add_error(None, "This product already exists.")
        else:
            print(form.errors)
    else:
        form = ProductForm()
    return render(request, 'products.html', {'form': form})
       
    
class DjTradersCustomersView(ListView):
    model = Customer
    template_name = 'DjTraders/customers.html'
    context_object_name = 'customers'
    #paginate_by=15
    
    def all_countries(self):
        Countries = self.model.objects.all().order_by('country').distinct()
        return Countries.values('country')
    
    def all_cities(self):
        Cities = self.model.objects.all().order_by('city').distinct()
        return Cities.values('city')
    
    def get_queryset(self):
       
        
        customerQuery = self.request.GET.get('srchCustomerName', '')
        countryQuery = self.request.GET.get('srchCountry', '')
        cityQuery = self.request.GET.get('srchCity', '')
        contactQuery = self.request.GET.get('srchContactName', '')
        
        if customerQuery:
            customers = self.model.objects.filter(
                customer_name__icontains=customerQuery
            )
        elif countryQuery:
            customers = self.model.objects.filter(
                country__icontains=countryQuery
            )
        elif cityQuery:
            customers = self.model.objects.filter(
                city__icontains=cityQuery
            )
        elif contactQuery:
            customers = self.model.objects.filter(
                contact_name__icontains=contactQuery
            )
        else:
            customers = self.model.objects.all()
            
        return customers.order_by("customer_name")
    
    def get_context_data(self, **kwargs):
       
        
        #1. Get the default context (list of objects)
        context = super().get_context_data(**kwargs)
        
        #2. Get the value for the input field "CustomerName"
        searchTermForCustomerName = self.request.GET.get('srchCustomerName', '')
        searchTermForCountry = self.request.GET.get('srchCountry', '')
        searchTermForCity = self.request.GET.get('srchCity', '')
        searchTermForContactName = self.request.GET.get('srchContactName', '')
        
        #3 Add variables back to the context with the same key as the field name
        context["srchCustomerName"] = searchTermForCustomerName
        context["srchCountry"] = searchTermForCountry
        context["srchCity"] = searchTermForCity
        context["srchContactName"] = searchTermForContactName
        
        context['Countries'] = self.all_countries()
        context['Cities'] = self.all_cities()
        
        
        #4. Give back the modified context dictionary.
        return context

    #V3.0

class CustomerOrders(ListView):
    model = Customer
    template_name = 'DjTraders/customer_orders.html'
    context_object_name = 'customer_orders'
    
    def CustomerNumOrdersPlot(self):
        CustomersWithOrders = Customer.objects.all().annotate(
            nOrders = Count('order')
        ).order_by('nOrders').reverse()
        
        TopTenCustomersWithOrders = CustomersWithOrders[:10]
        nCustomers =  CustomersWithOrders[:10].count()
        
        customer_names = [0 for _ in range(nCustomers)]
        NumberOfOrdersPlaced = [0 for _ in range(nCustomers)]
        index = 0
        
        for cOrder in TopTenCustomersWithOrders:
            customer_names[index] = cOrder.customer_name
            NumberOfOrdersPlaced[index] = cOrder.nOrders
            index = index+1
        
       
        fig = px.bar(
          x= customer_names,
          y= NumberOfOrdersPlaced,
          color_continuous_scale=px.colors.sequential.Jet,
          color=NumberOfOrdersPlaced,
          labels={'color':'Number Of Orders'},
          height=600,
          width=1000,
          text_auto=True,
        )
        
        fig.update_layout(
          title = 'Top 10 Customers by Number of Orders Placed',
          xaxis_title="Customer",
          yaxis_title="Number Of Orders",
        )
        
        # More on Plotly colors is here: https://plotly.com/python/builtin-colorscales/
        
              
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html

    def NCustomerOrders(self):
        CustomersWithOrders = Customer.objects.all().annotate(
            nOrders = Count('order')
        ).order_by('nOrders').reverse()
        
        TopTenCustomersWithOrders = CustomersWithOrders[:10].values('customer_name', 'nOrders')
        
        nCustomers =  CustomersWithOrders[:10].count()

        dFrame = pd.DataFrame(
            list(TopTenCustomersWithOrders),
            #columns=["Customer Name", "Number Of Orders"]
        )
        print(dFrame)
        
        fig = px.bar(
            dFrame,
            x= 'customer_name',
            y= 'nOrders',
            color_continuous_scale=px.colors.sequential.Jet,
            color="nOrders",
            labels={'color':'nOrders'},
            height=600,
            width=1000,
            text_auto=True,
        )
        
        fig.update_layout(
          title = 'Top 10 Customers by Number of Orders Placed',
          xaxis_title="Customer",
          yaxis_title="Number Of Orders",
        )
        
        # More on Plotly colors is here: https://plotly.com/python/builtin-colorscales/
        
              
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html

        
    
    
    def get_queryset(self):
        return super().get_queryset()

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CustomerOrderPlot"] = self.CustomerNumOrdersPlot()
        context["NCustomerOrdersPlot"] = self.NCustomerOrders()

                
        return context
    
    

# region Customer Detail View with a OrdersPlaced plot
# v3.0 Added
class DjTradersCustomerDetailView(DetailView):
    model=Customer
    template_name=  'DjTraders/customerDetail.html'
    context_object_name='customer'
    
    

    # v3.0 Added
    def OrdersPlacedPlot(self):
        

        # for more on the "get_object()" function, see: https://docs.djangoproject.com/en/5.1/ref/class-based-views/mixins-single-object/
        
        #get the specific customer object 
        theCustomer = self.get_object()
        
        #CustomerOrders() member function returns a queryset of all orders placed by theCustomer.
        customerOrders = theCustomer.CustomerOrders()

        # Create arrays to hold data 
        number_Of_Orders = customerOrders.count()
        order_dates = [0 for _ in range(number_Of_Orders)]
        order_totals = [0 for _ in range(number_Of_Orders)]
        order_ids = [0 for _ in range(number_Of_Orders)]
        index = 0
        
        # for each order in customerOrders, extract, dates, totals and id in each order.
        for order in customerOrders:
            order_ids[index] = order.order_id
            order_dates[index] = order.order_date
            order_totals[index] = order.OrderTotal()
            index = index+1
        
        # Create the bar chart - x and y are required, 
        # others are optional formatting.
        fig = px.bar(
            x=order_dates,
            y= order_totals,
            
            color=order_ids,
            labels={'color':'Order'},
            height=500,
            text_auto=True,
        )
        
        figure_title = 'Order Totals by Date <br><sup> for '  + theCustomer.customer_name + '</sup>'
        
        # Format Chart and Axes titles 
        fig.update_layout(
            title = figure_title,
            xaxis_title="Order Date",
            yaxis_title="Order Total",
        )
        
        # Colors and formats - remove legend.
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_tickprefix = '$', 
            yaxis_tickformat = ',.2f'
        )
        
        # generate the plot with the figure embedded as a Div
        plot_html = plot(fig, output_type='div')
        
        #return the html to place in the context and display
        return plot_html

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        
        # Add the plot to the context to make it available to the template.
        context['OrdersPlot'] = self.OrdersPlacedPlot()
        return context
    
# endregion
# v3.1 Added
# Return a partial view of the Customer's Orders Placed.

def OrdersPlaced(request):
    str_id = request.GET.get('customer_id')
    id=int(str_id)          
    customer = Customer.objects.get(customer_id=id)
    return render(request, 'DjTraders/_OrdersPlaced.html', 
                  {'customer': customer})

# v3.2 Orders By Date Plot 
def OrdersByDate(request, selOrderYear=""):
    # extract the customer_id and selected Order Year from the request.
    # the customer ID is converted to integer from the default string for I/O
    str_customer_id = request.GET.get('customer_id')
    customer_id=int(str_customer_id)
    selOrderYear = request.GET.get('selOrderYear')
    
    #use the customer_id to get the right customer.
    customer = Customer.objects.get(customer_id=customer_id)

    # To fill the dropdown, ask the Order Model for all distinct Years an Order was placed BY ANY customer.
    OrderYears = Order.AllOrderYears()
        
    
    TheAnnualOrders = customer.AnnualOrders()
    ordersByDatePlot = customer.OrdersPlacedPlot(selOrderYear)
    
    return render(
        request, 
        'DjTraders/_OrdersByDate.html', 
        {
            'customer': customer,
            'selOrderYear': selOrderYear,
            'OrderYears': OrderYears,
            'OrdersByDatePlot': ordersByDatePlot,
            'AnnualOrdersPlot': TheAnnualOrders,
        }
    )
    
# v3.2 Orders By Product Plot 
def OrdersByProduct(request):
    
    # extract the customer_id and selected Order Year from the request.
    # the customer ID is converted to integer from the default string for I/O
    str_customer_id = request.GET.get('customer_id')
    customer_id=int(str_customer_id)
    
    #use the customer_id to get the right customer.
    customer = Customer.objects.get(customer_id=customer_id)

    TheProductsRevenuePlot = customer.ProductReveues()
    TheProductsPlot = customer.ProductsSoldPlot()
    
    return render(
        request, 
        'DjTraders/_OrdersByProduct.html', 
        {
            'customer': customer,
            'ProductsPlot': TheProductsPlot,
            'ProductsRevenuePlot': TheProductsRevenuePlot,
        }
    )

# v3.2 Orders By Category Plot 
def OrdersByCategory(request):
    
    # extract the customer_id and selected Order Year from the request.
    # the customer ID is converted to integer from the default string for I/O
    str_customer_id = request.GET.get('customer_id')
    customer_id=int(str_customer_id)
    
    #use the customer_id to get the right customer.
    customer = Customer.objects.get(customer_id=customer_id)

    TheCategoryPlot = customer.ProductCategorySalesPlot()
    TheCategoryRevenusPlot = customer.ProductCategoryRevenusPlot()
    
    return render(
        request, 
        'DjTraders/_OrdersByCategory.html', 
        {
            'customer': customer,
            'CategoryRevenuesPlot': TheCategoryRevenusPlot,
            'CategoryPlot': TheCategoryPlot,
        }
    )

# endregion

     
class DjTradersProductDetailView(DetailView):
    model=Product
    template_name=  'DjTraders/productDetail.html'
    context_object_name='product'



    
    
 


# v2.1 
# Add the view class with the model, the form class and route for a successful submission.  
class DjTradersCustomerCreate(CreateView):
    model = Customer
    form_class= CustomerForm
    template_name='DjTraders/customer_form2.html'
    success_url='/DjTraders/Customers'
class DjTradersProductCreate(CreateView):
    model = Product
    form_class= ProductForm
    template_name='DjTraders/product_form2.html'
    success_url='/DjTraders/Products'
  
class DjTradersCustomerEdit(UpdateView):
    model=Customer
    form_class = CustomerForm
    success_url = '/DjTraders/Customers'

class DjTradersProductEdit(UpdateView):
    model=Product
    form_class = ProductForm
    template_name = 'DjTraders/product_form.html'
    success_url = '/DjTraders/Products'

#Note - you do not need this - unless you are doing extra credit.
class DjTradersCustomerDelete(DeleteView):
    model=Customer
    success_url = '/DjTraders/Customers'
    template_name='DjTraders/customer_delete.html'
  ##assgn extra  
class DjTradersCustomerSpendings(ListView):
    model=Customer
    success_url = '/DjTraders/Customers'
    template_name='DjTraders/CustomerSpendings.html'
    
class DjTradersProductDelete(DeleteView):
    model=Product
    success_url = '/DjTraders/Products'
    template_name='DjTraders/product_delete.html'
    
class DjTradersProdsPurchasedView(DetailView):
    model = Product
    template_name = 'DjTraders/prodsPurchasedDetail.html'
    context_object_name = 'product'
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        purchase_summary = product.customer_purchase_summary()
        context['purchase_summary'] = purchase_summary
        return context

#V3.0
#endregion

class CustomersListJSON(View):
    
    def get(self, request):
        
        allCustomerData = Customer.objects.all().annotate(
            nOrders = Count('order')
        ).order_by('nOrders').reverse()
            

        x = allCustomerData.values('customer_name', 'country', 'nOrders')[:10]
        
        
        CustomerData = list(x)#serialize("json", allCustomerData)
        
        # print(CustomerData)        
        return JsonResponse(CustomerData, safe=False)


# endregion









 

