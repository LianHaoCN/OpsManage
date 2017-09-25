

/* 2017-09-19 ,增加项目配置表字段*/
USE opsmanage ;

ALTER TABLE opsmanage_project_config  ADD project_prebuild_type SMALLINT(6) DEFAULT '0' COMMENT "是否需要预编译，0为否，1为是";
ALTER TABLE opsmanage_project_config  ADD project_prebuild_address VARCHAR(100) DEFAULT NULL COMMENT "预编译仓库地址";
ALTER TABLE opsmanage_project_config  ADD project_prebuild_command LONGTEXT DEFAULT NULL COMMENT "预编译执行的命令";

/* 2017-09-20，增加预编码代码路径*/
USE opsmanage ;
ALTER TABLE opsmanage_project_config  ADD project_prebuild_dir varchar(100) NOT NULL COMMENT "预编译仓库代码路径";


/* 2017-09-20，增加预编码代码路径*/
USE opsmanage ;
ALTER TABLE opsmanage_project_config  ADD project_repo_type SMALLINT(6) DEFAULT '1' COMMENT "Git地址是否多个项目，0为否，1为是";

/* 2017-09-21，增加模板表*/
CREATE TABLE `opsmanage_project_template` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_env` varchar(50) NOT NULL,
    `project_name` varchar(100) NOT NULL,
    `project_local_command` longtext,
    `project_repo_dir` varchar(100) NOT NULL,
    `project_dir` varchar(100) NOT NULL,
    `project_exclude` longtext,
    `project_address` varchar(100) NOT NULL,
    `project_repo_user` varchar(50),
    `project_repo_passwd` varchar(50),
    `project_repertory` varchar(10) NOT NULL,
    `project_template_status` smallint,
    `project_remote_command` longtext,
    `project_user` varchar(50) NOT NULL,
    `project_model` varchar(10) NOT NULL,
    `project_prebuild_type` smallint,
    `project_prebuild_address` varchar(100) NOT NULL,
    `project_prebuild_command` longtext,
    `project_prebuild_dir` varchar(100) NOT NULL,
    `project_repo_type` smallint
    `project_remote_dir` varchar(100) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
