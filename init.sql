-- `users` 테이블 생성
CREATE TABLE `users` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(255) NOT NULL UNIQUE,
    `user_id` VARCHAR(255) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `phone` VARCHAR(20) NOT NULL UNIQUE,
    `birth` DATE NOT NULL,
    `gender` ENUM('male', 'female', 'other') NOT NULL,
    `height` DECIMAL(5,2) NOT NULL,
    `weight` DECIMAL(5,2) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- `exercise_types` 테이블 생성
CREATE TABLE `exercise_types` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL UNIQUE,
    `description` TEXT,
    PRIMARY KEY (`id`)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- `user_exercises` 테이블 생성
CREATE TABLE `user_exercises` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `date` DATE NOT NULL,
    `exercise_number` INT(11) NOT NULL,
    `exercise_type_id` INT(11) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`exercise_type_id`) REFERENCES `exercise_types`(`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- `exercise_items` 테이블 생성
CREATE TABLE `exercise_items` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_exercise_id` INT(11) NOT NULL,
    `exercise_name` VARCHAR(255) NOT NULL,
    `exercise_set` INT(11) NOT NULL,
    `exercise_weight` DECIMAL(5,2) NOT NULL,
    `exercise_count` INT(11) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`user_exercise_id`) REFERENCES `user_exercises`(`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- `exercise_recommendations` 테이블 생성
CREATE TABLE `exercise_recommendations` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `date` DATE NOT NULL,
    `recommendation` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO exercise_types (name, description) VALUES 
('upper_body', '상체 전체 운동'),
('chest', '가슴 운동'),
('back', '등 운동'),
('shoulder', '어깨 운동'),
('abs', '복근 운동'),
('arms', '팔 전체 운동'),
('biceps', '이두 운동'),
('triceps', '삼두 운동'),
('legs', '하체 운동');