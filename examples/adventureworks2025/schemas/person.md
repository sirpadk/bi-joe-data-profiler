<div style="background:#f4f5f7;color:#1f2328;padding:16px 22px;border-radius:8px;">

<a href="../index.md" style="color:#0b5cad">← AdventureWorks2025 Overview</a> · <a href="../beam-annotations.md" style="color:#0b5cad">BEAM✲ Annotations</a> · <a href="../how-to-read.md" style="color:#0b5cad">How to Read This Wiki</a>

# Person

<i>13 tables. Tables with a dashed outline in the diagram belong to another schema.</i>

## Data Stories

<table style="border-collapse:collapse;margin:8px 0;width:100%;">
<tr><th style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;background:#cfd5dd;color:#1f2328;font-weight:600;vertical-align:bottom;">Table</th><th style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;background:#cfd5dd;color:#1f2328;font-weight:600;vertical-align:bottom;">BEAM✲</th><th style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;background:#cfd5dd;color:#1f2328;font-weight:600;vertical-align:bottom;">Grain</th><th style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;background:#cfd5dd;color:#1f2328;font-weight:600;vertical-align:bottom;">Description</th><th style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;background:#cfd5dd;color:#1f2328;font-weight:600;vertical-align:bottom;">Sampled Rows</th><th style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;background:#cfd5dd;color:#1f2328;font-weight:600;vertical-align:bottom;">Columns</th></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-address.md" style="color:#0b5cad">Person.Address</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a> <a href="beam-annotations.md#t-rp" style="color:#0b5cad" title="Role-Playing: One dimension used in several roles, e.g. Employee as both salesperson and manager. Calendar is the most common one.">[RP]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each street address, with the city, state or province and postal code it belongs to</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Street address information for customers, employees, and vendors.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">19,614</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">9</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-addresstype.md" style="color:#0b5cad">Person.AddressType</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each purpose an address can have for a person, store or vendor, such as billing, shipping or home</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Types of addresses stored in the Address table.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">6</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">4</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-businessentity.md" style="color:#0b5cad">Person.BusinessEntity</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each identifier issued to a person, a store or a vendor, so that they can all share address and contact tables; no other facts are held</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Source of the ID that connects vendors, customers, and employees with address and contact information.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">20,777</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">3</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-businessentityaddress.md" style="color:#0b5cad">Person.BusinessEntityAddress</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-mv" style="color:#0b5cad" title="Multi-Valued: A bridge table that links a fact to several values of a dimension at once (many-to-many), often with a weighting factor.">[MV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each address that a person, store or vendor has for one purpose, such as billing or shipping; an entity and an address type together identify a row</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Cross-reference table mapping customers, vendors, and employees to their addresses.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">19,614</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">5</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-businessentitycontact.md" style="color:#0b5cad">Person.BusinessEntityContact</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-mv" style="color:#0b5cad" title="Multi-Valued: A bridge table that links a fact to several values of a dimension at once (many-to-many), often with a weighting factor.">[MV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each person who acts as a contact of a given type for a store or vendor; a person appears only once</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Cross-reference table mapping stores, vendors, and employees to people</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">909</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">5</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-contacttype.md" style="color:#0b5cad">Person.ContactType</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each role a contact person can have at a store or vendor, such as Accounting Manager or Export Administrator</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Lookup table containing the types of business entity contacts.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">20</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">3</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-countryregion.md" style="color:#0b5cad">Person.CountryRegion</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each country or region, identified by its two-letter ISO code</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Lookup table containing the ISO standard codes for countries and regions.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">238</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">3</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-emailaddress.md" style="color:#0b5cad">Person.EmailAddress</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each e-mail address of a person; every person has exactly one, because the number of rows equals the number of people</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Where to send a person email.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">19,972</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">5</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-password.md" style="color:#0b5cad">Person.Password</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each person who has sign-in credentials, holding a salted hash of the password and the salt</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One way hashed authentication information</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">19,972</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">5</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-person.md" style="color:#0b5cad">Person.Person</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each human being known to the company, whether employee, customer, store contact or vendor contact; PersonType tells which</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Human beings involved with AdventureWorks: employees, customer contacts, and vendor contacts.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">19,972</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">13</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-personphone.md" style="color:#0b5cad">Person.PersonPhone</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each telephone number of a person, with the type of number (cell, home or work); each person has exactly one number</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Telephone number and type of a person.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">19,972</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">4</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-phonenumbertype.md" style="color:#0b5cad">Person.PhoneNumberType</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each kind of telephone number a person can have; the three kinds are cell, home and work</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">Type of phone number of a person.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">3</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">3</td></tr>
<tr><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="../data-stories/person-stateprovince.md" style="color:#0b5cad">Person.StateProvince</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;"><a href="beam-annotations.md#t-cv" style="color:#0b5cad" title="Current Value: Keeps only the current value of each attribute. Changes overwrite the old value. Also called a type 1 slowly changing dimension.">[CV]</a></td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">One row for each state or province of a country or region, with the sales territory it belongs to</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:left;vertical-align:top;">State and province lookup table.</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">181</td><td style="padding:6px 10px;border:1px solid #d0d4da;background:#ffffff;color:#1f2328;text-align:right;vertical-align:top;">8</td></tr>
</table>

## Data Model

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e4e7eb", "primaryTextColor": "#1f2328", "primaryBorderColor": "#8b929a", "lineColor": "#6b7280", "secondaryColor": "#ffffff", "tertiaryColor": "#f4f5f7", "background": "#f4f5f7", "mainBkg": "#e4e7eb", "nodeBorder": "#8b929a"}}}%%
flowchart LR
    t_Person_Address["Person.Address"]
    t_Person_AddressType["Person.AddressType"]
    t_Person_BusinessEntity["Person.BusinessEntity"]
    t_Person_BusinessEntityAddress["Person.BusinessEntityAddress"]
    t_Person_BusinessEntityContact["Person.BusinessEntityContact"]
    t_Person_ContactType["Person.ContactType"]
    t_Person_CountryRegion["Person.CountryRegion"]
    t_Person_EmailAddress["Person.EmailAddress"]
    t_Person_Password["Person.Password"]
    t_Person_Person["Person.Person"]
    t_Person_PersonPhone["Person.PersonPhone"]
    t_Person_PhoneNumberType["Person.PhoneNumberType"]
    t_Person_StateProvince["Person.StateProvince"]
    t_HumanResources_Employee["HumanResources.Employee"]
    t_Person_BusinessEntity --- t_HumanResources_Employee
    t_Person_EmailAddress --- t_HumanResources_Employee
    t_Person_Password --- t_HumanResources_Employee
    t_Person_Person --- t_HumanResources_Employee
    t_Person_PersonPhone --- t_HumanResources_Employee
    t_HumanResources_EmployeeDepartmentHistory["HumanResources.EmployeeDepartmentHistory"]
    t_Person_BusinessEntity --- t_HumanResources_EmployeeDepartmentHistory
    t_Person_EmailAddress --- t_HumanResources_EmployeeDepartmentHistory
    t_Person_Password --- t_HumanResources_EmployeeDepartmentHistory
    t_Person_Person --- t_HumanResources_EmployeeDepartmentHistory
    t_Person_PersonPhone --- t_HumanResources_EmployeeDepartmentHistory
    t_HumanResources_EmployeePayHistory["HumanResources.EmployeePayHistory"]
    t_Person_BusinessEntity --- t_HumanResources_EmployeePayHistory
    t_Person_EmailAddress --- t_HumanResources_EmployeePayHistory
    t_Person_Password --- t_HumanResources_EmployeePayHistory
    t_Person_Person --- t_HumanResources_EmployeePayHistory
    t_Person_PersonPhone --- t_HumanResources_EmployeePayHistory
    t_HumanResources_JobCandidate["HumanResources.JobCandidate"]
    t_Person_BusinessEntity --- t_HumanResources_JobCandidate
    t_Person_EmailAddress --- t_HumanResources_JobCandidate
    t_Person_Password --- t_HumanResources_JobCandidate
    t_Person_Person --- t_HumanResources_JobCandidate
    t_Person_PersonPhone --- t_HumanResources_JobCandidate
    t_Person_BusinessEntityAddress --- t_Person_Address
    t_Person_StateProvince --- t_Person_Address
    t_Person_BusinessEntity --- t_Person_BusinessEntityAddress
    t_Person_EmailAddress --- t_Person_BusinessEntityAddress
    t_Person_Password --- t_Person_BusinessEntityAddress
    t_Person_Person --- t_Person_BusinessEntityAddress
    t_Person_PersonPhone --- t_Person_BusinessEntityAddress
    t_Sales_PersonCreditCard["Sales.PersonCreditCard"]
    t_Sales_PersonCreditCard --- t_Person_BusinessEntityAddress
    t_Person_AddressType --- t_Person_BusinessEntityAddress
    t_Person_BusinessEntity --- t_Person_BusinessEntityContact
    t_Sales_Store["Sales.Store"]
    t_Sales_Store --- t_Person_BusinessEntityContact
    t_Person_ContactType --- t_Person_BusinessEntityContact
    t_Person_BusinessEntity --- t_Person_EmailAddress
    t_Person_Password --- t_Person_EmailAddress
    t_Person_Person --- t_Person_EmailAddress
    t_Person_PersonPhone --- t_Person_EmailAddress
    t_Person_BusinessEntity --- t_Person_Password
    t_Person_Person --- t_Person_Password
    t_Person_PersonPhone --- t_Person_Password
    t_Person_BusinessEntity --- t_Person_Person
    t_Person_PersonPhone --- t_Person_Person
    t_Person_BusinessEntity --- t_Person_PersonPhone
    t_Person_PhoneNumberType --- t_Person_PersonPhone
    t_Person_CountryRegion --- t_Person_StateProvince
    t_Sales_SalesTerritory["Sales.SalesTerritory"]
    t_Sales_SalesTerritory --- t_Person_StateProvince
    t_Purchasing_ProductVendor["Purchasing.ProductVendor"]
    t_Person_BusinessEntity --- t_Purchasing_ProductVendor
    t_Purchasing_Vendor["Purchasing.Vendor"]
    t_Person_BusinessEntity --- t_Purchasing_Vendor
    t_Sales_CountryRegionCurrency["Sales.CountryRegionCurrency"]
    t_Person_CountryRegion --- t_Sales_CountryRegionCurrency
    t_Person_BusinessEntity --- t_Sales_PersonCreditCard
    t_Person_EmailAddress --- t_Sales_PersonCreditCard
    t_Person_Password --- t_Sales_PersonCreditCard
    t_Person_Person --- t_Sales_PersonCreditCard
    t_Person_PersonPhone --- t_Sales_PersonCreditCard
    t_Sales_SalesOrderHeader["Sales.SalesOrderHeader"]
    t_Person_Address --- t_Sales_SalesOrderHeader
    t_Person_BusinessEntityAddress --- t_Sales_SalesOrderHeader
    t_Sales_SalesPerson["Sales.SalesPerson"]
    t_Person_BusinessEntity --- t_Sales_SalesPerson
    t_Person_EmailAddress --- t_Sales_SalesPerson
    t_Person_Password --- t_Sales_SalesPerson
    t_Person_Person --- t_Sales_SalesPerson
    t_Person_PersonPhone --- t_Sales_SalesPerson
    t_Sales_SalesPersonQuotaHistory["Sales.SalesPersonQuotaHistory"]
    t_Person_BusinessEntity --- t_Sales_SalesPersonQuotaHistory
    t_Person_EmailAddress --- t_Sales_SalesPersonQuotaHistory
    t_Person_Password --- t_Sales_SalesPersonQuotaHistory
    t_Person_Person --- t_Sales_SalesPersonQuotaHistory
    t_Person_PersonPhone --- t_Sales_SalesPersonQuotaHistory
    t_Sales_SalesTaxRate["Sales.SalesTaxRate"]
    t_Person_StateProvince --- t_Sales_SalesTaxRate
    t_Person_CountryRegion --- t_Sales_SalesTerritory
    t_Sales_SalesTerritoryHistory["Sales.SalesTerritoryHistory"]
    t_Person_BusinessEntity --- t_Sales_SalesTerritoryHistory
    t_Person_EmailAddress --- t_Sales_SalesTerritoryHistory
    t_Person_Password --- t_Sales_SalesTerritoryHistory
    t_Person_Person --- t_Sales_SalesTerritoryHistory
    t_Person_PersonPhone --- t_Sales_SalesTerritoryHistory
    t_Person_BusinessEntity --- t_Sales_Store
    classDef ext stroke-dasharray:4 3,fill:none
    class t_HumanResources_Employee,t_HumanResources_EmployeeDepartmentHistory,t_HumanResources_EmployeePayHistory,t_HumanResources_JobCandidate,t_Sales_PersonCreditCard,t_Sales_Store,t_Sales_SalesTerritory,t_Purchasing_ProductVendor,t_Purchasing_Vendor,t_Sales_CountryRegionCurrency,t_Sales_SalesOrderHeader,t_Sales_SalesPerson,t_Sales_SalesPersonQuotaHistory,t_Sales_SalesTaxRate,t_Sales_SalesTerritoryHistory ext
```

---

## Metadata

_Machine-readable facts about this page, for tools and AI agents._

```yaml
bijoe: "schema"
schema_version: 2
dataset: "AdventureWorks2025"
schema: "Person"
tables: 13
generated_at: "2026-11-22T20:13:24+00:00"
```

</div>
