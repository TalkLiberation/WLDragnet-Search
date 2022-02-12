create table files
(
    id serial not null
        constraint files_pk
            primary key,
    file_url varchar not null,
    archive_url varchar not null,
    nodexl_id integer not null,
    description varchar,
    timestamp varchar not null
);

alter table files owner to postgres;

create unique index files_file_url_uindex
    on files (file_url);

create table graphs
(
    id serial not null
        constraint graphs_pk
            primary key,
    name varchar not null,
    file_id integer not null
        constraint graphs_files_id_fk
            references files
);

alter table graphs owner to postgres;

create table ranked_handles
(
    id serial not null
        constraint ranked_handles_pk
            primary key,
    rank integer not null,
    type varchar not null,
    handle varchar not null,
    graph_id integer not null
        constraint ranked_handles_graphs_id_fk
            references graphs
);

alter table ranked_handles owner to postgres;

create unique index ranked_handles_rank_type_graph_id_uindex
    on ranked_handles (rank, type, graph_id);

create table ranked_urls
(
    id serial not null
        constraint ranked_urls_pk
            primary key,
    rank integer not null,
    url varchar not null,
    graph_id integer not null
        constraint ranked_urls_graphs_id_fk
            references graphs
);

alter table ranked_urls owner to postgres;

create unique index ranked_urls_rank_graph_id_uindex
    on ranked_urls (rank, graph_id);

create table ranked_domains
(
    id serial not null
        constraint ranked_domains_pk
            primary key,
    rank integer not null,
    domain varchar not null,
    graph_id integer not null
        constraint ranked_domains_graphs_id_fk
            references graphs
);

alter table ranked_domains owner to postgres;

create unique index ranked_domains_rank_graph_id_uindex
    on ranked_domains (rank, graph_id);

create table ranked_hashtags
(
    id serial not null
        constraint ranked_hashtags_pk
            primary key,
    rank integer not null,
    hashtag varchar not null,
    graph_id integer not null
        constraint ranked_hashtags_graphs_id_fk
            references graphs
);

alter table ranked_hashtags owner to postgres;

create unique index ranked_hashtags_rank_graph_id_uindex
    on ranked_hashtags (rank, graph_id);

create table ranked_words
(
    id serial not null
        constraint ranked_words_pk
            primary key,
    rank integer not null,
    word varchar not null,
    graph_id integer not null
        constraint ranked_words_graphs_id_fk
            references graphs
);

alter table ranked_words owner to postgres;

create unique index ranked_words_rank_graph_id_uindex
    on ranked_words (rank, graph_id);

create table ranked_word_pairs
(
    id serial not null
        constraint ranked_word_pairs_pk
            primary key,
    rank integer not null,
    word1 varchar not null,
    word2 varchar not null,
    graph_id integer not null
        constraint ranked_word_pairs_graphs_id_fk
            references graphs
);

alter table ranked_word_pairs owner to postgres;

create unique index ranked_word_pairs_graph_id_rank_uindex
    on ranked_word_pairs (graph_id, rank);

create unique index graphs_id_uindex
    on graphs (id);

create unique index graphs_name_file_id_uindex
    on graphs (name, file_id);

