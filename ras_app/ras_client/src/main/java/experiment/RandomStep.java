package experiment;

import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.net.InetSocketAddress;
import java.util.Random;
import java.util.concurrent.ExecutionException;

import Server.SimpleTask;
import app.Client;
import net.spy.memcached.MemcachedClient;

public class RandomStep implements Runnable {

	private Integer tick = null;
	private SimpleTask workGenerator = null;
	private Random rnd=null;
	private MemcachedClient memClient=null;

	public RandomStep(SimpleTask workGenerator) {
		this.tick = 0;
		this.workGenerator = workGenerator;
		this.rnd=new Random();
		try {
			this.memClient = new MemcachedClient(new InetSocketAddress(this.workGenerator.getJedisHost(), 11211));
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	private void addClients(int delta) {
		int actualSize = this.workGenerator.getThreadpool().getCorePoolSize();
		try {
			this.workGenerator.setThreadPoolSize(actualSize+delta);
		} catch (Exception e1) {
			e1.printStackTrace();
		}
		if (delta >= 0) {
			for (int i = 0; i < delta; i++) {
				Constructor<? extends Runnable> c;
				try {
					c = Client.class.getDeclaredConstructor(SimpleTask.class, Long.class);
					this.workGenerator.getThreadpool().submit(c.newInstance(this.workGenerator, this.workGenerator.getsTimes()
							.get(this.workGenerator.getEntries().entrySet().iterator().next().getKey())));
				} catch (NoSuchMethodException | SecurityException | InstantiationException | IllegalAccessException
						| IllegalArgumentException | InvocationTargetException e) {
					e.printStackTrace();
				}
			}
		} else {
			if (Math.abs(delta) > actualSize) {
				System.err.println(String.format("Error killing clients %d-%d", actualSize, Math.abs(delta)));
			}
			try {
				Client.setToKill(Math.abs(delta));
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
	}

	private void tick() {
		int nc=0;
		if (this.tick % 150 == 0) {
			if(this.rnd.nextBoolean()) {
				nc=this.rnd.nextInt(100-this.workGenerator.getThreadpool().getCorePoolSize());
				System.out.println(String.format("delta clients %d-%d", nc,this.workGenerator.getThreadpool().getCorePoolSize()));
				this.addClients(nc);
			}else {
				nc=this.rnd.nextInt(this.workGenerator.getThreadpool().getCorePoolSize());
				System.out.println(String.format("delta clients %d-%d", -nc,this.workGenerator.getThreadpool().getCorePoolSize()));
				this.addClients(-nc);
			}
			try {
				this.memClient.set("sim", 3600,"step").get();
			} catch (InterruptedException | ExecutionException e) {
				e.printStackTrace();
			}
		}
		this.tick++;
	}

	@Override
	public void run() {
		this.tick();
	}
}
