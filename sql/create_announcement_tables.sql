-- 创建公告表和可见性表
-- 如果表已存在，先删除
DROP TABLE IF EXISTS announcement_visibility;
DROP TABLE IF EXISTS announcement;

-- 创建公告表
CREATE TABLE announcement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    time_str DATETIME NOT NULL
)ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建公告可见性表
CREATE TABLE announcement_visibility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    announcement_id INT NOT NULL,
    target_type ENUM('student', 'college', 'major') NOT NULL,
    target_id VARCHAR(255) NOT NULL,
    FOREIGN KEY (announcement_id) REFERENCES announcement(id)
        ON DELETE CASCADE
)ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

