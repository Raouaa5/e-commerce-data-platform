CREATE OR REPLACE VIEW staging.order_reviews AS
WITH ranked AS (
    SELECT
        review_id,
        order_id,
        review_score::integer                   AS review_score,
        review_comment_title                    AS comment_title,
        review_comment_message                  AS comment_message,
        review_creation_date::timestamp         AS created_at,
        review_answer_timestamp::timestamp      AS answered_at,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY review_answer_timestamp::timestamp DESC, review_id
        ) AS rn
    FROM raw.order_reviews
)
SELECT
    review_id,
    order_id,
    review_score,
    comment_title,
    comment_message,
    created_at,
    answered_at
FROM ranked
WHERE rn = 1;