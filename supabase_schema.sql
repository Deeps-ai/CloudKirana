-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Business Table
CREATE TABLE businesses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    role TEXT NOT NULL, -- 'retailer', 'wholesaler', 'manufacturer'
    ondc_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone TEXT UNIQUE NOT NULL,
    business_id UUID REFERENCES businesses(id),
    role TEXT NOT NULL, -- 'retailer', 'consumer', 'authority', 'wholesaler'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products Table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    gtin TEXT,
    mrp DECIMAL,
    net_qty TEXT,
    manufacturer TEXT,
    category TEXT,
    is_compliant BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compliance Checks Table
CREATE TABLE compliance_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id),
    business_id UUID REFERENCES businesses(id),
    evidence_image_url TEXT,
    extracted_fields JSONB,
    verdict TEXT NOT NULL, -- 'COMPLIANT', 'POTENTIAL_ISSUE', 'REQUIRES_VERIFICATION'
    flagged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved BOOLEAN DEFAULT false
);

-- Inventory Items Table
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(id),
    product_id UUID REFERENCES products(id),
    quantity INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(business_id, product_id)
);

-- Invoices Table
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(id),
    supplier_name TEXT,
    extracted_items JSONB,
    confidence DECIMAL,
    status TEXT DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Orders Table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    consumer_id UUID REFERENCES users(id),
    store_id UUID REFERENCES businesses(id),
    items JSONB NOT NULL,
    total DECIMAL NOT NULL,
    status TEXT DEFAULT 'Placed', -- 'Placed', 'Verified & Packed', 'Out for Delivery', 'Delivered'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
