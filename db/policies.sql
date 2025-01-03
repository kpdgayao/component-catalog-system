-- Enable RLS on tables
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;

-- Categories policies
CREATE POLICY "Enable read access for all users" ON public.categories
    FOR SELECT
    USING (true);

CREATE POLICY "Enable insert for authenticated users" ON public.categories
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users" ON public.categories
    FOR UPDATE
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users" ON public.categories
    FOR DELETE
    USING (auth.role() = 'authenticated');

-- Tags policies
CREATE POLICY "Enable read access for all users" ON public.tags
    FOR SELECT
    USING (true);

CREATE POLICY "Enable insert for authenticated users" ON public.tags
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users" ON public.tags
    FOR UPDATE
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users" ON public.tags
    FOR DELETE
    USING (auth.role() = 'authenticated');

-- Add unique constraints to prevent duplicate names
ALTER TABLE public.categories ADD CONSTRAINT categories_name_key UNIQUE (name);
ALTER TABLE public.tags ADD CONSTRAINT tags_name_key UNIQUE (name);
