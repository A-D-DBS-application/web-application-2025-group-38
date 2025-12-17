CREATE TABLE public.ArtistGenres (
  artist_id bigint NOT NULL,
  genre_id bigint NOT NULL,
  CONSTRAINT ArtistGenres_pkey PRIMARY KEY (artist_id, genre_id),
  CONSTRAINT ArtistGenres_artist_id_fkey FOREIGN KEY (artist_id) REFERENCES public.Artists(id),
  CONSTRAINT ArtistGenres_genre_id_fkey FOREIGN KEY (genre_id) REFERENCES public.Genres(id)
);
CREATE TABLE public.Artists (
  id bigint NOT NULL DEFAULT nextval('"Artists_id_seq"'::regclass),
  created_at timestamp without time zone NOT NULL,
  Artist_name character varying NOT NULL,
  image_url character varying,
  edition_id integer NOT NULL,
  CONSTRAINT Artists_pkey PRIMARY KEY (id),
  CONSTRAINT Artists_edition_id_fkey FOREIGN KEY (edition_id) REFERENCES public.FestivalEdition(id)
);
CREATE TABLE public.FestivalEdition (
  id integer NOT NULL DEFAULT nextval('"FestivalEdition_id_seq"'::regclass),
  created_at timestamp with time zone DEFAULT now(),
  Start_date date,
  End_date date,
  Name text,
  Location text,
  is_active boolean NOT NULL DEFAULT true,
  CONSTRAINT FestivalEdition_pkey PRIMARY KEY (id)
);
CREATE TABLE public.Genres (
  id bigint NOT NULL DEFAULT nextval('"Genres_id_seq"'::regclass),
  name character varying NOT NULL UNIQUE,
  related_genre_id bigint,
  CONSTRAINT Genres_pkey PRIMARY KEY (id),
  CONSTRAINT Genres_related_genre_id_fkey FOREIGN KEY (related_genre_id) REFERENCES public.Genres(id)
);
CREATE TABLE public.Polloption (
  id integer NOT NULL DEFAULT nextval('"Polloption_id_seq"'::regclass),
  created_at timestamp with time zone DEFAULT now(),
  text text,
  Count integer,
  artist_id integer,
  poll_id integer,
  CONSTRAINT Polloption_pkey PRIMARY KEY (id),
  CONSTRAINT Polloption_artist_id_fkey FOREIGN KEY (artist_id) REFERENCES public.Artists(id),
  CONSTRAINT Polloption_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.poll(id)
);
CREATE TABLE public.Suggestion_feedback (
  id integer NOT NULL DEFAULT nextval('"Suggestion_feedback_id_seq"'::regclass),
  artist_id integer,
  user_id integer,
  festival_id integer,
  created_at timestamp with time zone DEFAULT now(),
  is_hidden boolean NOT NULL DEFAULT false,
  CONSTRAINT Suggestion_feedback_pkey PRIMARY KEY (id),
  CONSTRAINT Suggestion_feedback_artist_id_fkey FOREIGN KEY (artist_id) REFERENCES public.Artists(id),
  CONSTRAINT Suggestion_feedback_festival_id_fkey FOREIGN KEY (festival_id) REFERENCES public.FestivalEdition(id),
  CONSTRAINT Suggestion_feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.User(id)
);
CREATE TABLE public.User (
  id integer NOT NULL DEFAULT nextval('"User_id_seq"'::regclass),
  created_at timestamp with time zone DEFAULT now(),
  email text,
  is_admin boolean NOT NULL DEFAULT false,
  CONSTRAINT User_pkey PRIMARY KEY (id)
);
CREATE TABLE public.Votes_for (
  created_at timestamp with time zone DEFAULT now(),
  user_id integer NOT NULL,
  polloption_id integer NOT NULL,
  CONSTRAINT Votes_for_pkey PRIMARY KEY (user_id, polloption_id),
  CONSTRAINT Votes_for_polloption_id_fkey FOREIGN KEY (polloption_id) REFERENCES public.Polloption(id),
  CONSTRAINT Votes_for_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.User(id)
);
CREATE TABLE public.alembic_version (
  version_num character varying NOT NULL,
  CONSTRAINT alembic_version_pkey PRIMARY KEY (version_num)
);
CREATE TABLE public.poll (
  id integer NOT NULL DEFAULT nextval('poll_id_seq'::regclass),
  created_at timestamp with time zone DEFAULT now(),
  Question text,
  festival_id integer,
  is_visible boolean NOT NULL DEFAULT true,
  show_results boolean NOT NULL DEFAULT true,
  CONSTRAINT poll_pkey PRIMARY KEY (id),
  CONSTRAINT poll_festival_id_fkey FOREIGN KEY (festival_id) REFERENCES public.FestivalEdition(id)
);
