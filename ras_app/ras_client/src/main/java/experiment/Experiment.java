package experiment;

import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.net.InetSocketAddress;
import java.util.Random;

import Server.SimpleTask;
import app.Client;
import net.spy.memcached.MemcachedClient;

public abstract class Experiment implements Runnable{
	Integer tick = null;
	SimpleTask workGenerator = null;
	Random rnd=null;
	MemcachedClient memClient=null;
	
	public Experiment(SimpleTask workGenerator) {
		this.tick = 0;
		this.workGenerator = workGenerator;
		this.rnd=new Random();
		try {
			this.memClient = new MemcachedClient(new InetSocketAddress(this.workGenerator.getJedisHost(), 11211));
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	public void addClients(int delta) {
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
	
	public abstract void tick();
	
}
