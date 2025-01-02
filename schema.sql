-- Part 1: Create the trigger function first
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Part 2: Create tables and other objects
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist
DROP TABLE IF EXISTS usage_statistics CASCADE;
DROP TABLE IF EXISTS sample_applications CASCADE;
DROP TABLE IF EXISTS implementation_examples CASCADE;
DROP TABLE IF EXISTS features CASCADE;
DROP TABLE IF EXISTS component_tags CASCADE;
DROP TABLE IF EXISTS components CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS tags CASCADE;

-- Drop existing triggers
DROP TRIGGER IF EXISTS update_components_updated_at ON components;

-- Categories Table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tags Table
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Components Table
CREATE TABLE components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('Frontend', 'Backend', 'Full Stack')),
    original_project VARCHAR(200),
    version VARCHAR(50),
    category_id UUID REFERENCES categories(id),
    primary_developers TEXT[],
    documentation_status VARCHAR(50) CHECK (documentation_status IN ('Complete', 'Partial', 'Needs Update')),
    description TEXT,
    technology_stack TEXT[],
    dependencies TEXT[],
    aws_services TEXT[],
    auth_requirements TEXT,
    db_requirements TEXT,
    api_endpoints JSONB,
    test_coverage DECIMAL,
    has_unit_tests BOOLEAN DEFAULT false,
    has_integration_tests BOOLEAN DEFAULT false,
    has_e2e_tests BOOLEAN DEFAULT false,
    known_limitations TEXT,
    performance_metrics JSONB,
    update_frequency VARCHAR(100),
    breaking_changes_history JSONB,
    backward_compatibility_notes TEXT,
    support_contact TEXT,
    setup_instructions TEXT,
    configuration_requirements TEXT,
    integration_patterns TEXT,
    troubleshooting_guide TEXT,
    business_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Component Tags Junction Table
CREATE TABLE component_tags (
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (component_id, tag_id)
);

-- Features Table
CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) CHECK (status IN ('Ready', 'In Progress', 'Planned')),
    complexity VARCHAR(50) CHECK (complexity IN ('Low', 'Medium', 'High')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Implementation Examples Table
CREATE TABLE implementation_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    project_name VARCHAR(200) NOT NULL,
    use_case TEXT,
    customizations TEXT,
    implementation_hours INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sample Applications Table
CREATE TABLE sample_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    industry VARCHAR(200),
    use_case TEXT,
    required_customization TEXT,
    estimated_hours INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Usage Statistics Table
CREATE TABLE usage_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    project_name VARCHAR(200),
    usage_date DATE,
    usage_type VARCHAR(50),
    usage_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_components_category ON components(category_id);
CREATE INDEX idx_component_tags_component ON component_tags(component_id);
CREATE INDEX idx_component_tags_tag ON component_tags(tag_id);
CREATE INDEX idx_features_component ON features(component_id);
CREATE INDEX idx_implementation_component ON implementation_examples(component_id);
CREATE INDEX idx_sample_apps_component ON sample_applications(component_id);
CREATE INDEX idx_usage_stats_component ON usage_statistics(component_id);

-- Part 3: Create trigger after tables exist
CREATE TRIGGER update_components_updated_at
    BEFORE UPDATE ON components
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
