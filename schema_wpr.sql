-- Weekly Progress Report (WPR) Schema

-- Team Members Table
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    team VARCHAR(100) NOT NULL,
    role VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Reports Table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_member_id UUID REFERENCES team_members(id),
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    completed_tasks TEXT[] NOT NULL,
    pending_tasks TEXT[] NOT NULL,
    dropped_tasks TEXT[],
    projects JSONB[], -- Array of {name: string, completion: number}
    productivity_rating INTEGER NOT NULL,
    productivity_suggestions TEXT[],
    productivity_details TEXT,
    productive_time VARCHAR(100),
    productive_place VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_member_id, week_number, year)
);

-- HR Analysis Table
CREATE TABLE IF NOT EXISTS hr_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    team_member_id UUID REFERENCES team_members(id),
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    analysis_text TEXT NOT NULL,
    metrics JSONB NOT NULL,
    recommendations TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Peer Evaluations Table
CREATE TABLE IF NOT EXISTS peer_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    evaluator_id UUID REFERENCES team_members(id),
    evaluatee_id UUID REFERENCES team_members(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(report_id, evaluator_id, evaluatee_id)
);

-- Create updated_at triggers
CREATE TRIGGER update_team_members_updated_at
    BEFORE UPDATE ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hr_analysis_updated_at
    BEFORE UPDATE ON hr_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_peer_evaluations_updated_at
    BEFORE UPDATE ON peer_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
