create table instagram_account
(
    id         VARCHAR(30) primary key not null,
    name       VARCHAR(50),
    enabled    integer default true    not null,
    deleted_at datetime
);

create table instagram_read_history
(
    id          INTEGER primary key                not null,
    post_id     VARCHAR(15)                        not null,
    account_id  VARCHAR(30)                        not null
        references instagram_account,
    is_festival INTEGER,
    posted_at   datetime                           not null,
    created_at  datetime default current_timestamp not null
);

create index ix_instagram_read_history_account_id
    on instagram_read_history (account_id);

create index ix_instagram_read_history_post_id
    on instagram_read_history (post_id);

create index ix_instagram_read_history_posted_at_desc
    on instagram_read_history (posted_at desc);
