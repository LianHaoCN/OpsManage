

/* 2017-09-19 ,增加项目配置表字段*/
USE opsmanage ;

ALTER TABLE opsmanage_project_config  ADD project_prebuild_type SMALLINT(6) DEFAULT '0' COMMENT "是否需要预编译，0为否，1为是";
ALTER TABLE opsmanage_project_config  ADD project_prebuild_address VARCHAR(100) DEFAULT NULL COMMENT "预编译仓库地址";
ALTER TABLE opsmanage_project_config  ADD project_prebuild_command LONGTEXT DEFAULT NULL COMMENT "预编译执行的命令";

/* 2017-09-20，增加预编码代码路径*/
USE opsmanage ;
ALTER TABLE opsmanage_project_config  ADD project_prebuild_dir varchar(100) NOT NULL COMMENT "预编译仓库代码路径";
