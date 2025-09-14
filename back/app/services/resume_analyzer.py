# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : back
file name : resume_analyzer
Author : Administrator
date : 2025/09/12  15:45
'''
import re
from typing import List, Dict, Any
from app.models import ContactInfo, WorkExperience, ProjectExperience, Skill, AnalysisResult


class ResumeAnalyzer:
    """简历分析器"""

    @staticmethod
    def extract_contact_info(text: str) -> ContactInfo:
        """提取联系信息"""
        contact_info = {}

        # 提取姓名
        name_patterns = [
            r"姓名[：:]\s*(\S+)",
            r"个人简介[：:][\s\S]*?姓名[：:]\s*(\S+)",
            r"^(\S+)\s+简历",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                contact_info["name"] = match.group(1)
                break

        # 提取职位和经验
        position_pattern = r"(?:职位|岗位|目前职位)[：:]\s*([^\n]+)"
        match = re.search(position_pattern, text)
        if match:
            contact_info["position"] = match.group(1)

        # 提取工作经验年限
        exp_pattern = r"(?:工作经验|工作年限)[：:]\s*([^\n]+)"
        match = re.search(exp_pattern, text)
        if match:
            contact_info["experience"] = match.group(1)

        # 提取电话
        phone_pattern = r"1[3-9]\d{9}"
        match = re.search(phone_pattern, text)
        if match:
            contact_info["phone"] = match.group(0)

        # 提取邮箱
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, text)
        if match:
            contact_info["email"] = match.group(0)

        # 提取个人简介
        intro_pattern = r"(?:个人简介|自我评价|关于我)[：:\n]([\s\S]*?)(?=\n\s*\n|$|工作经历|项目经历|教育经历|技能)"
        match = re.search(intro_pattern, text, re.IGNORECASE)
        if match:
            contact_info["introduction"] = match.group(1).strip()

        return contact_info

    @staticmethod
    def extract_work_experiences(text: str) -> List[Dict[str, Any]]:
        """提取工作经历"""
        experiences = []

        # 查找工作经历部分
        work_section_pattern = r"(?:工作经历|工作经验|职业经历)[：:\n]([\s\S]*?)(?=\n\s*\n|$|项目经历|教育经历|技能|自我评价)"
        match = re.search(work_section_pattern, text, re.IGNORECASE)

        if not match:
            return experiences

        work_section = match.group(1)

        # 分割每个工作经历
        work_items = re.split(r"\n\s*\n", work_section.strip())

        for item in work_items:
            if not item.strip():
                continue

            # 尝试提取公司、职位和时间信息
            company_pattern = r"(?:公司|企业|组织)[：:]\s*([^\n]+)"
            position_pattern = r"(?:职位|岗位|职务)[：:]\s*([^\n]+)"
            time_pattern = r"(\d{4}年\d{1,2}月\s*[-至]\s*\d{4}年\d{1,2}月|至今|\d{4}/\d{1,2}\s*[-至]\s*\d{4}/\d{1,2})"

            company_match = re.search(company_pattern, item)
            position_match = re.search(position_pattern, item)
            time_match = re.search(time_pattern, item)

            experience = {
                "company": company_match.group(1) if company_match else "未知公司",
                "position": position_match.group(1) if position_match else "未知职位",
            }

            if time_match:
                time_str = time_match.group(1)
                if "至今" in time_str:
                    experience["end_date"] = "至今"
                    start_match = re.search(r"(\d{4}年\d{1,2}月|\d{4}/\d{1,2})", time_str)
                    if start_match:
                        experience["start_date"] = start_match.group(1)
                else:
                    dates = re.split(r"[-至]", time_str)
                    if len(dates) >= 2:
                        experience["start_date"] = dates[0].strip()
                        experience["end_date"] = dates[1].strip()

            experiences.append(experience)

        return experiences

    @staticmethod
    def extract_project_experiences(text: str) -> List[Dict[str, Any]]:
        """提取项目经历"""
        projects = []

        # 查找项目经历部分
        project_section_pattern = r"(?:项目经历|项目经验|参与项目)[：:\n]([\s\S]*?)(?=\n\s*\n|$|工作经历|教育经历|技能|自我评价)"
        match = re.search(project_section_pattern, text, re.IGNORECASE)

        if not match:
            return projects

        project_section = match.group(1)

        # 分割每个项目
        project_items = re.split(r"\n\s*\n", project_section.strip())

        for item in project_items:
            if not item.strip():
                continue

            # 提取项目名称
            name_pattern = r"项目(?:名称|名)[：:]\s*([^\n]+)"
            name_match = re.search(name_pattern, item)

            if name_match:
                project = {"name": name_match.group(1)}

                # 提取角色
                role_pattern = r"(?:角色|职责|担任)[：:]\s*([^\n]+)"
                role_match = re.search(role_pattern, item)
                if role_match:
                    project["role"] = role_match.group(1)

                # 提取时间
                time_pattern = r"时间[：:]\s*([^\n]+)"
                time_match = re.search(time_pattern, item)
                if time_match:
                    project["time_period"] = time_match.group(1)

                # 提取技术栈
                tech_pattern = r"(?:技术|工具|使用技术)[：:]\s*([^\n]+)"
                tech_match = re.search(tech_pattern, item)
                if tech_match:
                    project["technologies"] = [t.strip() for t in tech_match.group(1).split('、') if t.strip()]

                # 提取描述
                desc_pattern = r"(?:描述|详情|项目介绍)[：:]\s*([^\n]+)"
                desc_match = re.search(desc_pattern, item)
                if desc_match:
                    project["description"] = desc_match.group(1)

                projects.append(project)

        return projects

    @staticmethod
    def extract_skills(text: str) -> List[Dict[str, Any]]:
        """提取技能信息"""
        skills = []

        # 查找技能部分
        skill_section_pattern = r"(?:技能|专业技能|技术技能|能力)[：:\n]([\s\S]*?)(?=\n\s*\n|$|工作经历|项目经历|教育经历|自我评价)"
        match = re.search(skill_section_pattern, text, re.IGNORECASE)

        if not match:
            return skills

        skill_section = match.group(1)

        # 尝试按类别分割技能
        categories = re.split(r"\n\s*([^：:\n]+)[：:]\s*", skill_section)

        if len(categories) > 1:
            for i in range(1, len(categories), 2):
                category = categories[i].strip()
                items_str = categories[i + 1].strip() if i + 1 < len(categories) else ""

                # 分割技能项
                items = []
                if "、" in items_str:
                    items = [item.strip() for item in items_str.split('、') if item.strip()]
                elif "," in items_str:
                    items = [item.strip() for item in items_str.split(',') if item.strip()]
                else:
                    items = [item.strip() for item in items_str.split() if item.strip()]

                if items:
                    skills.append({"category": category, "items": items})
        else:
            # 如果没有明确的类别，将所有技能放入一个类别
            all_skills = re.split(r"[、,，\n]", skill_section)
            items = [skill.strip() for skill in all_skills if skill.strip()]
            if items:
                skills.append({"category": "专业技能", "items": items})

        return skills

    @staticmethod
    def generate_career_timeline(work_experiences: List[Dict[str, Any]]) -> str:
        """生成职业发展时间线"""
        if not work_experiences:
            return "暂无工作经历信息"

        timeline = "职业发展历程:\n"
        for i, exp in enumerate(work_experiences, 1):
            timeline += f"{i}. {exp.get('start_date', '未知')} - {exp.get('end_date', '未知')}: "
            timeline += f"{exp.get('position', '未知职位')} @ {exp.get('company', '未知公司')}\n"

        return timeline

    @staticmethod
    def generate_project_summary(project_experiences: List[Dict[str, Any]]) -> str:
        """生成项目总结与复盘"""
        if not project_experiences:
            return "暂无项目经历信息"

        summary = "项目总结与复盘:\n"
        for i, project in enumerate(project_experiences, 1):
            summary += f"\n项目{i}: {project.get('name', '未知项目')}\n"
            summary += f"  角色: {project.get('role', '未知')}\n"
            summary += f"  时间: {project.get('time_period', '未知')}\n"
            if project.get('technologies'):
                summary += f"  使用技术: {', '.join(project['technologies'])}\n"
            if project.get('description'):
                summary += f"  项目描述: {project['description']}\n"

        return summary

    @staticmethod
    def extract_core_skills(skills: List[Dict[str, Any]]) -> List[str]:
        """提取核心技能"""
        core_skills = []
        for skill_category in skills:
            core_skills.extend(skill_category.get("items", []))
        return core_skills[:10]  # 返回前10个作为核心技能