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
DROP TABLE IF EXISTS technical_specifications CASCADE;
DROP TABLE IF EXISTS component_tags CASCADE;
DROP TABLE IF EXISTS component_files CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS version_history CASCADE;
DROP TABLE IF EXISTS components CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- Categories Table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tags Table
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Components Table
CREATE TABLE components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),  -- Frontend/Backend/Full Stack
    original_project VARCHAR(255),
    version VARCHAR(50),
    primary_developers TEXT[],
    documentation_status VARCHAR(50),
    description TEXT,
    technology_stack TEXT[],
    dependencies TEXT[],
    aws_services TEXT[],
    auth_requirements TEXT,
    db_requirements TEXT,
    api_endpoints TEXT,
    test_coverage INTEGER,
    has_unit_tests BOOLEAN DEFAULT false,
    has_integration_tests BOOLEAN DEFAULT false,
    has_e2e_tests BOOLEAN DEFAULT false,
    known_limitations TEXT,
    performance_metrics TEXT,
    update_frequency VARCHAR(100),
    breaking_changes_history TEXT,
    backward_compatibility_notes TEXT,
    support_contact TEXT,
    business_value JSONB,
    setup_instructions TEXT,
    configuration_requirements TEXT,
    integration_patterns TEXT,
    troubleshooting_guide TEXT,
    category_id UUID REFERENCES categories(id),
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Component Files Table
CREATE TABLE component_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    description TEXT,
    uploaded_by UUID,
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

-- Version History Table
CREATE TABLE version_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    version_number VARCHAR(50) NOT NULL,
    change_description TEXT,
    changed_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Features Table
CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    complexity VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Implementation Examples Table
CREATE TABLE implementation_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,
    use_case TEXT,
    customizations TEXT,
    implementation_time INTEGER, -- in hours
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sample Applications Table
CREATE TABLE sample_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    industry VARCHAR(255),
    use_case TEXT,
    required_customization TEXT,
    estimated_time INTEGER, -- in hours
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Usage Statistics Table
CREATE TABLE usage_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    project_count INTEGER DEFAULT 0,
    total_usage_hours INTEGER DEFAULT 0,
    average_implementation_time INTEGER, -- in hours
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_components_category ON components(category_id);
CREATE INDEX idx_component_tags_component ON component_tags(component_id);
CREATE INDEX idx_component_tags_tag ON component_tags(tag_id);
CREATE INDEX idx_component_files_component ON component_files(component_id);
CREATE INDEX idx_version_history_component ON version_history(component_id);
CREATE INDEX idx_features_component ON features(component_id);
CREATE INDEX idx_implementation_component ON implementation_examples(component_id);
CREATE INDEX idx_sample_apps_component ON sample_applications(component_id);
CREATE INDEX idx_usage_stats_component ON usage_statistics(component_id);

-- Enable RLS and add policies
ALTER TABLE components ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE component_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE component_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE features ENABLE ROW LEVEL SECURITY;
ALTER TABLE implementation_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE sample_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_statistics ENABLE ROW LEVEL SECURITY;

-- Add policies for authenticated users
CREATE POLICY "Enable read access for authenticated users" ON components
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert access for authenticated users" ON components
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update access for authenticated users" ON components
    FOR UPDATE
    USING (auth.role() = 'authenticated');

-- Similar policies for other tables
CREATE POLICY "Enable read access for authenticated users" ON categories
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable read access for authenticated users" ON tags
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all access for authenticated users" ON component_tags
    FOR ALL
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all access for authenticated users" ON component_files
    FOR ALL
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all access for authenticated users" ON features
    FOR ALL
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all access for authenticated users" ON implementation_examples
    FOR ALL
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all access for authenticated users" ON sample_applications
    FOR ALL
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all access for authenticated users" ON usage_statistics
    FOR ALL
    USING (auth.role() = 'authenticated');

-- Insert some initial categories
INSERT INTO categories (name, description) VALUES
    ('UI Components', 'Reusable user interface components'),
    ('API Services', 'Backend API services and endpoints'),
    ('Data Processing', 'Components for data processing and transformation'),
    ('Authentication', 'Authentication and authorization components'),
    ('Integration', 'Third-party integration components');

-- Insert some initial tags
INSERT INTO tags (name, description) VALUES
    ('React', 'React.js components'),
    ('Python', 'Python-based components'),
    ('AWS', 'AWS-integrated components'),
    ('Database', 'Database-related components'),
    ('API', 'API-related components'),
    ('Security', 'Security-focused components');

-- Add is_archived column to components table if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'components' 
        AND column_name = 'is_archived'
    ) THEN 
        ALTER TABLE components 
        ADD COLUMN is_archived BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Create triggers for updated_at
CREATE TRIGGER update_components_updated_at
    BEFORE UPDATE ON components
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tags_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_component_files_updated_at
    BEFORE UPDATE ON component_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
