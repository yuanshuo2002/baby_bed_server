-- 添加 family_id 字段到 devices 表
-- 用于标识设备所属的家庭

ALTER TABLE devices ADD COLUMN family_id BIGINT NULL AFTER device_sn;

-- 添加索引以提高查询性能
ALTER TABLE devices ADD INDEX idx_devices_family_id (family_id);

-- 将已绑定设备的 family_id 设置为对应宝宝的 family_id
-- 注意：此语句需要确保 Baby 表中 baby_id 对应的 family_id 存在
UPDATE devices d
INNER JOIN baby b ON d.baby_id = b.id
SET d.family_id = b.family_id
WHERE d.baby_id IS NOT NULL AND d.family_id IS NULL;
