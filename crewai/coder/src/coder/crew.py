from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from .tools.pdf_reader_tool import PDFReaderTool
@CrewBase
class CVGeneratorCrew():
    """CV generator crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def cv_extractor(self) -> Agent:
        return Agent(
            config = self.agents_config['cv_extractor'],
            verbose = True,
            tools = [PDFReaderTool()]
        )
    
    @agent
    def cv_formatter(self) -> Agent:
        return Agent(
            config = self.agents_config['cv_formatter'],
            verbose = True,
        )
    
    @agent
    def pdf_generator(self) -> Agent:
        return Agent(
            config = self.agents_config['pdf_generator'],
            verbose = True,
        )
    
    @task
    def extract_task(self) -> Task:
        return Task(
            config = self.tasks_config['extract_task'],
        )
    
    @task
    def format_task(self) -> Task:
        return Task(
            config = self.tasks_config['format_task'],
        )

    @task
    def generate_task(self) -> Task:
        return Task(
            config = self.tasks_config['generate_task'],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents = self.agents,
            tasks = self.tasks,
            process=Process.sequential,
            verbose=True
        )