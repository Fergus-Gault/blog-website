DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS favourite;

CREATE TABLE user (
    id BIGINT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    admin BIT NOT NULL DEFAULT 0,
    emailConfirmed BIT NOT NULL DEFAULT 0
);

CREATE TABLE post (
    id BIGINT PRIMARY KEY,
    author_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE comment (
    commentID BIGINT PRIMARY KEY,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    body TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user (id)
    FOREIGN KEY (post_id) REFERENCES post (id)
);

CREATE TABLE favourite (
    id BIGINT PRIMARY KEY,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user (id)
    FOREIGN KEY (post_id) REFERENCES post (id)
);