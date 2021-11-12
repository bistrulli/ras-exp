package experiment;

import java.util.concurrent.ExecutionException;

import Server.SimpleTask;

public class SinGen extends Experiment{ 
	
	private Double mod=null;
	private Double period=null;

	public SinGen(SimpleTask workGenerator,double mod, double period) {
		super(workGenerator);
		this.mod=mod;
		this.period= period/ (2*Math.PI);
	}

	@Override
	public void run() {
		this.tick();
	}

	@Override
	public void tick() {
		if (this.tick % 10 == 0) {
			int nc=Double.valueOf(Math.cos(this.tick/this.period)*this.mod).intValue();
			if(nc<0 && Math.abs(nc)>this.workGenerator.getThreadpool().getCorePoolSize()-20){
				nc=0;
			}
			System.out.println(String.format("delta clients %d-%d", nc,this.workGenerator.getThreadpool().getCorePoolSize()));
			this.addClients(nc);
			try {
				this.memClient.set("sim", 3600,"step").get();
			} catch (InterruptedException | ExecutionException e) {
				e.printStackTrace();
			}
		}
		this.tick++;
	}

}
