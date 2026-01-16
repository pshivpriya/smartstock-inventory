const BASE_URL="http://127.0.0.1:5000";

fetch(`${BASE_URL}/products`)
.then(res=>res.json())
.then(products=>{
 let low=0, value=0;
 products.forEach(p=>{
   value+=p.quantity*p.costPrice;
   if(p.quantity<p.lowStock) low++;
 });
 document.getElementById("lowStock").innerText=low;
 document.getElementById("inventoryValue").innerText=value;
});
